"""
cache.py — In-Memory & External Cache Utilities

Purpose:
- Provide a simple caching layer for repeated lookups:
    * Company metadata lookups (ticker → id)
    * Recent model runs
    * Resolved GAAP tag mappings (future)
- For MVP: use in-process Python dict (non-distributed, non-persistent).
- Later upgrade path:
    * Redis (for multi-instance deployments)
    * TTL-based expiring cache
    * Soft invalidation (e.g., after successful ingestion refresh)

This module should be a *utility helper*, not a stateful service.

Key Notes:
- Because the MVP does not run multiple worker instances, in-memory cache is acceptable.
- Cache keys should be deterministic: (table_name, primary_key) or structured strings.

This module does NOT:
- Connect to Redis (yet).
- Store large historical datasets — keep cache small & targeted.
"""

from typing import Any, Dict, Tuple

# -----------------------------------------------------------------------------
# Simple In-Memory Cache (MVP)
# -----------------------------------------------------------------------------

# Key: str identifier
# Value: arbitrary cached object
_cache_store: Dict[str, Any] = {}


def make_key(namespace: str, identifier: Any) -> str:
    """
    Utility to construct consistent cache keys.

    Example:
        make_key("company", 52) → "company:52"
    """
    return f"{namespace}:{identifier}"


def cache_get(key: str) -> Any:
    """
    Retrieve cached object if present.
    Returns None if not cached.
    """
    return _cache_store.get(key)


def cache_set(key: str, value: Any) -> None:
    """
    Store object in cache. No TTL in MVP.
    """
    _cache_store[key] = value


def cache_clear(namespace: str = None) -> None:
    """
    Clears cache entirely, or optionally clears only a specific namespace.

    Example:
        cache_clear("company") clears keys starting with "company:"
    """
    if namespace is None:
        _cache_store.clear()
    else:
        prefix = f"{namespace}:"
        for key in list(_cache_store.keys()):
            if key.startswith(prefix):
                del _cache_store[key]
