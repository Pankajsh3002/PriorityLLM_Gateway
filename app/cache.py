import hashlib
import json
import uuid
import numpy as np

TTL_S = 3600


def exact_key(tenant: str, alias: str, messages: list, params: dict) -> str:
    blob = json.dumps([alias, messages, params], sort_keys=True)
    return f"gw:cache:{tenant}:" + hashlib.sha256(blob.encode()).hexdigest()


def cacheable(params: dict) -> bool:
    # Only deterministic requests are safe to reuse.
    return (params.get("temperature") or 0) == 0


async def get_exact(r, key: str):
    raw = await r.get(key)
    return json.loads(raw) if raw else None


async def put_exact(r, key: str, entry: dict):
    await r.set(key, json.dumps(entry), ex=TTL_S)


class SemanticCache:
    """Reuse answers for *similar* prompts. `embed` maps str -> 1-D vector."""

    def __init__(self, r, embed, threshold: float = 0.92):
        self.r, self.embed, self.threshold = r, embed, threshold

    @staticmethod
    def _unit(v):
        v = np.asarray(v, dtype=np.float32)
        return v / (np.linalg.norm(v) + 1e-9)

    async def get(self, tenant: str, alias: str, prompt: str):
        vecs = await self.r.hgetall(f"gw:sem:{tenant}:{alias}")
        if not vecs:
            return None
        ids = list(vecs.keys())
        mat = np.stack(
            [np.frombuffer(vecs[i], dtype=np.float32) for i in ids]
        )
        sims = mat @ self._unit(self.embed(prompt))
        best = int(np.argmax(sims))
        if sims[best] < self.threshold:
            return None
        raw = await self.r.get(f"gw:sem:resp:{ids[best].decode()}")
        return (json.loads(raw), float(sims[best])) if raw else None

    async def put(self, tenant: str, alias: str, prompt: str, entry: dict):
        sid = uuid.uuid4().hex
        await self.r.hset(
            f"gw:sem:{tenant}:{alias}",
            sid,
            self._unit(self.embed(prompt)).tobytes(),
        )
        await self.r.set(f"gw:sem:resp:{sid}", json.dumps(entry), ex=TTL_S)
