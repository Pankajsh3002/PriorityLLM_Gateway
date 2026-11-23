import asyncio
import redis.asyncio as aioredis
from app.providers import MockProvider
from app.router import Router


async def main():
    r = aioredis.from_url("redis://localhost:6379/0")
    await r.flushdb()
    router = Router(
        r, MockProvider(r, median_s=0.01), {"fast": ["mock-a", "mock-b"]}
    )
    msgs = [{"role": "user", "content": "hi"}]
    _, model = await router.call("fast", msgs)
    print("healthy ->", model)
    await r.set("gw:mock:fail:mock-a", 1.0)  # simulate an outage of mock-a
    for i in range(4):
        _, model = await router.call("fast", msgs)
        print(
            f"mock-a down #{i+1} ->",
            model,
            "| breaker open:",
            bool(await r.exists("gw:cb:open:mock-a")),
        )
    await r.flushdb()
    await r.aclose()


if __name__ == "__main__":
    asyncio.run(main())
