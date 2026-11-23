import asyncio
import numpy as np
import redis.asyncio as aioredis
from app.cache import SemanticCache

VOCAB = [
    "refund",
    "return",
    "policy",
    "shipping",
    "invoice",
    "password",
    "reset",
]


def fake_embed(text: str):
    """Bag-of-words stand-in so the test runs without downloading a model."""
    v = np.array([float(w in text.lower()) for w in VOCAB]) + 1e-3
    return v


async def main():
    r = aioredis.from_url("redis://localhost:6379/0")
    sc = SemanticCache(r, fake_embed, threshold=0.9)
    await sc.put(
        "t1",
        "fast",
        "what is your refund policy",
        {"response": "30 days", "cost": 0.001},
    )
    near = await sc.get("t1", "fast", "refund policy please")
    far = await sc.get("t1", "fast", "how do I reset my password")
    other_tenant = await sc.get("t2", "fast", "what is your refund policy")
    print(
        "near-duplicate hit :",
        near is not None,
        f"(sim={near[1]:.2f})" if near else "",
    )
    print("unrelated prompt :", "miss" if far is None else "WRONG HIT")
    print(
        "other tenant :",
        "miss (isolated)" if other_tenant is None else "LEAK",
    )
    await r.aclose()


if __name__ == "__main__":
    asyncio.run(main())
