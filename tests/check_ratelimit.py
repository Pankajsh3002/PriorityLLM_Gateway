import asyncio
import redis.asyncio as aioredis
from app.ratelimit import RateLimiter


async def main():
    r = aioredis.from_url("redis://localhost:6379/0")
    await r.delete("gw:rl:check")
    rl = RateLimiter(r)
    results = [await rl.allow("check", rpm=60, burst=3) for _ in range(5)]
    print(
        [
            ("allowed" if ok else f"blocked, retry in {wait:.1f}s")
            for ok, wait in results
        ]
    )
    await asyncio.sleep(1.1)  # 60 rpm = 1 token per second
    print("after 1.1s:", await rl.allow("check", rpm=60, burst=3))
    await r.aclose()


if __name__ == "__main__":
    asyncio.run(main())
