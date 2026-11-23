import asyncio
import redis.asyncio as aioredis
from app.scheduler import enqueue, dequeue


async def main():
    r = aioredis.from_url("redis://localhost:6379/0")
    await r.delete("gw:queue")
    await enqueue(r, "batch-1", {"n": 1}, "batch")
    await asyncio.sleep(0.01)  # batch really arrived first
    await enqueue(r, "standard-1", {"n": 2}, "standard")
    await enqueue(r, "interactive-1", {"n": 3}, "interactive")
    order = []
    for _ in range(3):
        req_id, _payload = await dequeue(r)
        order.append(req_id)
    print("served order:", order)
    assert order == ["interactive-1", "standard-1", "batch-1"]
    print("OK: higher priority jumps ahead even though batch arrived first")
    await r.aclose()


if __name__ == "__main__":
    asyncio.run(main())
