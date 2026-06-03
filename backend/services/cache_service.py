import time
import hashlib
import json

# TTL tính bằng giây
PREDICT_TTL = 3600   # 1 giờ
OLAP_TTL = 21600     # 6 giờ

_store: dict[str, dict] = {}


def _make_key(prefix: str, data: dict) -> str:
    raw = json.dumps(data, sort_keys=True)
    h = hashlib.md5(raw.encode()).hexdigest()
    return f"{prefix}:{h}"


def get(prefix: str, data: dict):
    key = _make_key(prefix, data)
    entry = _store.get(key)
    if entry is None:
        return None
    if time.time() > entry["expires_at"]:
        del _store[key]
        return None
    return entry["value"]


def set(prefix: str, data: dict, value, ttl: int = PREDICT_TTL):
    key = _make_key(prefix, data)
    _store[key] = {
        "value": value,
        "expires_at": time.time() + ttl,
    }


def stats() -> dict:
    now = time.time()
    valid = sum(1 for e in _store.values() if e["expires_at"] > now)
    return {"total_entries": len(_store), "valid_entries": valid}