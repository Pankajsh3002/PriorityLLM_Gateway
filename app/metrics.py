from prometheus_client import Counter, Gauge, Histogram

BUCKETS = (0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10, 30, 60)

REQUESTS = Counter(
    "gw_requests_total",
    "Requests",
    ["tenant", "priority", "status", "cache"],
)
LATENCY = Histogram(
    "gw_request_seconds",
    "End-to-end latency",
    ["priority"],
    buckets=BUCKETS,
)
QUEUE_WAIT = Histogram(
    "gw_queue_wait_seconds",
    "Time spent queued",
    ["priority"],
    buckets=BUCKETS,
)
QUEUE_DEPTH = Gauge("gw_queue_depth", "Jobs waiting in the queue")
TOKENS = Counter("gw_tokens_total", "Tokens used", ["tenant", "model", "kind"])
COST = Counter("gw_cost_usd_total", "Spend in USD", ["tenant", "model"])
SAVED = Counter("gw_cache_saved_usd_total", "USD saved by cache", ["tenant"])
FALLBACKS = Counter(
    "gw_fallbacks_total",
    "Fallback to a non-primary model",
    ["alias", "model_used"],
)
CIRCUIT_OPEN = Counter(
    "gw_circuit_skips_total",
    "Calls skipped because the breaker was open",
    ["model"],
)
PROVIDER_ERRORS = Counter(
    "gw_provider_errors_total",
    "Upstream errors",
    ["model", "status"],
)
