import asyncio
import math
import random
import time
import uuid
import httpx

class ProviderError(Exception):
    """Base class for provider-related errors."""
    def __init__(self, msg: str,status: int = 502):
        super().__init__(msg)
        self.status = status

def _fake_usage(messages:list, text:str):
    """Simulate usage metrics for a given text and messages."""
    # Count tokens in the text and messages
    text_tokens = len(text.split())
    messages_tokens = sum(len(m["content"].split()) for m in messages)
    total_tokens = text_tokens + messages_tokens


    return {
        "prompt_tokens": messages_tokens,
        "completion_tokens": text_tokens,
        "total_tokens": total_tokens,
    }


class MockProvider:
    def __init__(self, r, median_s: float = 0.6, sigma: float = 0.4):
        self.r = r
        self.mu = math.log(median_s)
        self.sigma = sigma

    async def complete(self,model, messages, **params):
        fail = float(await self.r.get(f"gw:mock:fail:{model}") or 0)
        await asyncio.sleep(random.lognormvariate(self.mu, self.sigma))
        if random.random() < fail:
            raise ProviderError(f"{model} simulated outage", 503)
        text = f"[{model}] echo: " + messages[-1]["content"][:200]
        return {
        "id": "mock-" + uuid.uuid4().hex[:12],
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [{"index": 0, "finish_reason": "stop",
        "message": {"role": "assistant", "content": text}}],
        "usage": _fake_usage(messages, text),
        }

class OpenRouterProvider:
    URL = "https://openrouter.ai/api/v1/chat/completions"
    def __init__(self, api_key: str):
        self.client = httpx.AsyncClient(timeout=60)
        self.headers = {"Authorization": f"Bearer {api_key}",
        "X-Title": "llm-gateway-portfolio"}

    async def complete(self, model, messages, **params):
        body = {"model": model, "messages": messages, **params}
        resp = await self.client.post(self.URL, json=body, headers=self.headers)
        if resp.status_code in (429, 500, 502, 503, 504):
            raise ProviderError(f"{model}: HTTP {resp.status_code}", resp.status_code)
        if resp.status_code >= 400:
        # 4xx (bad request, no credits) will not be fixed by retrying
            raise ProviderError(resp.text[:300], resp.status_code)
        return resp.json()
