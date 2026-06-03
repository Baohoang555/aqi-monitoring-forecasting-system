import time
from collections import defaultdict

_counters: dict[str, int] = defaultdict(int)
_latencies: dict[str, list[float]] = defaultdict(list)


def record_request(endpoint: str):
    _counters[f"{endpoint}.total"] += 1


def record_cache_hit(endpoint: str):
    _counters[f"{endpoint}.cache_hit"] += 1


def record_cache_miss(endpoint: str):
    _counters[f"{endpoint}.cache_miss"] += 1


def record_latency(endpoint: str, seconds: float):
    _latencies[endpoint].append(seconds)
    if len(_latencies[endpoint]) > 1000:
        _latencies[endpoint] = _latencies[endpoint][-1000:]


def get_metrics() -> dict:
    result = dict(_counters)
    for endpoint, times in _latencies.items():
        if not times:
            continue
        sorted_times = sorted(times)
        n = len(sorted_times)
        result[f"{endpoint}.latency_p50"] = round(sorted_times[int(n * 0.50)], 4)
        result[f"{endpoint}.latency_p95"] = round(sorted_times[int(n * 0.95)], 4)
        result[f"{endpoint}.latency_p99"] = round(sorted_times[min(int(n * 0.99), n - 1)], 4)
    return result