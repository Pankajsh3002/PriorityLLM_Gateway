# Token bucket implemented as one Lua script so the read-modify-write is
# atomic even with many gateway processes. Redis TIME is the single clock.
TOKEN_BUCKET_LUA = """
local key = KEYS[1]
local rate = tonumber(ARGV[1]) -- tokens added per second
local burst = tonumber(ARGV[2]) -- bucket capacity
local cost = tonumber(ARGV[3])
local t = redis.call('TIME')
local now = tonumber(t[1]) + tonumber(t[2]) / 1000000
local d = redis.call('HMGET', key, 'tokens', 'ts')
local tokens = tonumber(d[1])
local ts = tonumber(d[2])
if tokens == nil then tokens = burst; ts = now end
tokens = math.min(burst, tokens + (now - ts) * rate)
local allowed = 0
local retry_after = 0
if tokens >= cost then
 tokens = tokens - cost
 allowed = 1
else
 retry_after = (cost - tokens) / rate
end
redis.call('HSET', key, 'tokens', tokens, 'ts', now)
redis.call('EXPIRE', key, math.ceil(burst / rate) * 2 + 1)
return {allowed, tostring(retry_after)}
"""


class RateLimiter:
    def __init__(self, r):
        self._script = r.register_script(TOKEN_BUCKET_LUA)

    async def allow(self, tenant: str, rpm: int, burst: int):
        """Returns (allowed: bool, retry_after_seconds: float)."""
        res = await self._script(
            keys=[f"gw:rl:{tenant}"], args=[rpm / 60.0, burst, 1]
        )
        return bool(res[0]), float(res[1])
