import json
import time
from app.config import settings

QUEUE_KEY = "gw:queue"

# How many seconds of "head start" each tier gets in the queue.
# Lower score = served first. A batch job that has waited longer than the
# head start eventually beats a fresh interactive job, so nothing starves.
HEAD_START = {"interactive": 30.0, "standard": 10.0, "batch": 0.0}


async def enqueue(r, req_id: str, payload: dict, priority: str) -> None:
    now = time.time()
    payload = {**payload, "enqueued_at": now, "priority": priority}
    head = HEAD_START[priority] if settings.scheduling == "priority" else 0.0
    score = now - head
    pipe = r.pipeline()
    pipe.set(f"gw:job:{req_id}", json.dumps(payload), ex=300)
    pipe.zadd(QUEUE_KEY, {req_id: score})
    await pipe.execute()


async def dequeue(r, timeout: int = 1):
    """Block up to `timeout` s for the lowest-score job. Atomic across workers."""
    item = await r.bzpopmin(QUEUE_KEY, timeout=timeout)
    if item is None:
        return None
    _key, req_id, _score = item
    req_id = req_id.decode() if isinstance(req_id, bytes) else req_id
    raw = await r.get(f"gw:job:{req_id}")
    await r.delete(f"gw:job:{req_id}")
    if raw is None:  # job expired while queued
        return None
    return req_id, json.loads(raw)


async def queue_depth(r) -> int:
    return await r.zcard(QUEUE_KEY)
