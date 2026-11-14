"""Shared JSON fetch for the tools: in-process cache, retries with backoff, and errors that never echo
the URL (API keys travel in query strings)."""
import logging
import time

import httpx

logging.getLogger("httpx").setLevel(logging.WARNING)  # its INFO lines print full URLs, keys included
_cache = {}


def get_json(url, params=None, headers=None, post=None, timeout=20, tries=1):
    key = (url, repr(sorted((params or {}).items())), repr(post))
    if key in _cache:
        return _cache[key]
    for i in range(tries):
        try:
            r = httpx.request("POST" if post else "GET", url, params=params, headers=headers, json=post, timeout=timeout)
            if r.status_code == 200:
                if len(_cache) > 500:
                    _cache.clear()
                _cache[key] = r.json()
                return _cache[key]
            err = f"HTTP {r.status_code}"
        except (httpx.HTTPError, ValueError) as e:
            err = type(e).__name__
        if i < tries - 1:
            time.sleep(2 ** i)
    raise RuntimeError(f"{httpx.URL(url).host} failed: {err}")
