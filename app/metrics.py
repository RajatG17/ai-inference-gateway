from prometheus_client import Counter, Histogram

REQUEST_COUNT = Counter(
    "inference_requests_total",
    "Total inference requests received",
    ["tenant_id", "status"]
)

REQUEST_LATENCY = Histogram(
    "inference_request_latency_seconds",
    "Latency of inference requests in seconds",
    ["tenant_id"]
)

CACHE_HITS = Counter(
    "inference_cache_hits_total",
    "Cache hits",
    ["tenant_id"]
)
CACHE_MISSES = Counter(
    "inference_cache_misses_total",
    "Cache misses",
    ["tenant_id"]
)

RATE_LIMIT_HITS = Counter(
    "inference_rate_limit_hits_total",
    "Rate limit hits",
    ["tenant_id"]
)

ERROR_COUNT = Counter(
    "inference_errors_total",
    "Total inference errors",
    ["tenant_id", "error_type"]
)