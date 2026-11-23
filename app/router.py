import asyncio
import random
from app import metrics
from app.providers import ProviderError

FAIL_WINDOW_S = 30  # failures are counted inside this window
FAIL_THRESHOLD = 5  # this many failures opens the breaker
OPEN_FOR_S = 20  # how long the breaker stays open
RETRIABLE = {429, 500, 502, 503, 504}


class Router:
    def __init__(self, r, provider, routes: dict, attempts_per_model: int = 2):
        self.r, self.provider = r, provider
        self.routes, self.attempts = routes, attempts_per_model

    # ---- circuit breaker (state lives in Redis, shared by all workers) ----
    async def _is_open(self, model):
        return bool(await self.r.exists(f"gw:cb:open:{model}"))

    async def _record_failure(self, model):
        k = f"gw:cb:fail:{model}"
        n = await self.r.incr(k)
        if n == 1:
            await self.r.expire(k, FAIL_WINDOW_S)
        if n >= FAIL_THRESHOLD:
            await self.r.set(f"gw:cb:open:{model}", 1, ex=OPEN_FOR_S)

    async def _record_success(self, model):
        await self.r.delete(f"gw:cb:fail:{model}")

    # ---- routing with retries and fallback ----
    async def call(self, alias: str, messages: list, **params):
        candidates = self.routes.get(alias)
        if not candidates:
            raise ProviderError(f"unknown model alias '{alias}'", 400)
        last_err = None
        for i, model in enumerate(candidates):
            if await self._is_open(model):
                metrics.CIRCUIT_OPEN.labels(model).inc()
                continue
            for attempt in range(self.attempts):
                try:
                    resp = await self.provider.complete(
                        model, messages, **params
                    )
                    await self._record_success(model)
                    if i > 0:
                        metrics.FALLBACKS.labels(alias, model).inc()
                    return resp, model
                except ProviderError as e:
                    last_err = e
                    metrics.PROVIDER_ERRORS.labels(model, str(e.status)).inc()
                    if e.status in RETRIABLE:
                        await self._record_failure(model)
                    else:
                        raise  # 4xx: retrying will not help
                    if attempt + 1 < self.attempts:
                        await asyncio.sleep(
                            0.2 * 2**attempt + random.random() * 0.1
                        )
        raise last_err or ProviderError(
            "all models unavailable (breakers open)", 503
        )
