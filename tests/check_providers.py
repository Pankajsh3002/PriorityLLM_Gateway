import asyncio
import redis.asyncio as aioredis
from app.providers import MockProvider
async def main():
    r = aioredis.from_url("redis://localhost:6379/0")
    mock = MockProvider(r, median_s=0.05)
    resp = await mock.complete("mock-a", [{"role": "user", "content": "hello there"}])
    print(resp["choices"][0]["message"]["content"], "|", resp["usage"])
    await r.aclose()
    
asyncio.run(main())
