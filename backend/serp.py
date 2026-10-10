from __future__ import annotations
import hashlib, json, time
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any
import requests

SERPAPI_URL = "https://serpapi.com/search.json"
ENGINE_LABELS = {"google_maps": "Google Maps", "google_maps_reviews": "Maps reviews",
                 "google_jobs": "Google Jobs", "google_shopping": "Google Shopping",
                 "google_news": "Google News", "google": "Google Search"}
_EMPTY_HINTS = ("hasn't returned any results", "has not returned any results", "no results")

class SerpError(RuntimeError):
    pass

class _BaseClient:
    def __init__(self) -> None:
        self.trace: list[dict[str, Any]] = []
        self.searches_made = 0
        self.cache_hits = 0

    def _record(self, engine, purpose, query, status, ms, cached, results, note=""):
        self.trace.append({"step": len(self.trace) + 1, "engine": engine,
            "engine_label": ENGINE_LABELS.get(engine, engine), "purpose": purpose, "query": query,
            "status": status, "ms": ms, "cached": cached, "results": results,
            "followup": purpose in {"followup", "reviews"}, "note": note})

    def usage(self):
        return {"searches": self.searches_made, "cache_hits": self.cache_hits,
                "engines": sorted({t["engine"] for t in self.trace})}

def count_results(data: dict[str, Any]) -> int:
    for key in ("organic_results", "local_results", "news_results", "shopping_results", "jobs_results", "reviews"):
        v = data.get(key)
        if isinstance(v, list):
            return len(v)
        if isinstance(v, dict) and isinstance(v.get("places"), list):
            return len(v["places"])
    if isinstance(data.get("place_results"), dict):
        return 1
    return 0

class LiveSerpClient(_BaseClient):
    def __init__(self, api_key, cache_dir, ttl_hours=24, daily_limit=40, gl="in", hl="en",
                 google_domain="google.co.in", session=None):
        super().__init__()
        self.api_key = api_key
        self.cache_dir = Path(cache_dir); self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl = ttl_hours * 3600
        self.daily_limit = daily_limit
        self.gl, self.hl, self.google_domain = gl, hl, google_domain
        self.session = session or requests.Session()

    @property
    def _usage_file(self) -> Path:
        return self.cache_dir / "usage.json"

    def searches_today(self) -> int:
        try:
            data = json.loads(self._usage_file.read_text())
            return int(data.get(date.today().isoformat(), 0))
        except Exception:
            return 0

    def _bump_usage(self) -> None:
        today = date.today().isoformat()
        try:
            data = json.loads(self._usage_file.read_text())
        except Exception:
            data = {}
        data = {today: int(data.get(today, 0)) + 1}
        self._usage_file.write_text(json.dumps(data))

    def _cache_path(self, params) -> Path:
        clean = {k: v for k, v in params.items() if k != "api_key"}
        digest = hashlib.sha1(json.dumps(clean, sort_keys=True).encode()).hexdigest()
        return self.cache_dir / f"{digest}.json"

    def _read_cache(self, path: Path):
        try:
            if path.exists() and time.time() - path.stat().st_mtime < self.ttl:
                return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None
        return None

    def search(self, engine, purpose, **params):
        label = params.pop("label", "")
        query = label or str(params.get("q", ""))
        full = {"engine": engine, **params}
        if engine in {"google", "google_news", "google_shopping", "google_jobs"}:
            full.setdefault("gl", self.gl); full.setdefault("hl", self.hl)
        if engine in {"google", "google_shopping"}:
            full.setdefault("google_domain", self.google_domain)
        if engine == "google_maps":
            full.setdefault("type", "search"); full.setdefault("hl", self.hl)

        path = self._cache_path(full)
        started = time.time()
        cached = self._read_cache(path)
        if cached is not None:
            self.cache_hits += 1
            n = count_results(cached)
            self._record(engine, purpose, query, "ok" if n else "empty",
                          int((time.time() - started) * 1000), True, n, "served from cache")
            return cached

        if self.searches_today() >= self.daily_limit:
            self._record(engine, purpose, query, "error", 0, False, 0, "daily search limit reached")
            raise SerpError(f"Daily search guard reached ({self.daily_limit}). Raise "
                             "TRUSTLENS_DAILY_SEARCH_LIMIT in .env or try again tomorrow.")

        try:
            resp = self.session.get(SERPAPI_URL, params={**full, "api_key": self.api_key}, timeout=30)
        except requests.RequestException as exc:
            self._record(engine, purpose, query, "error", int((time.time() - started) * 1000), False, 0, str(exc)[:120])
            raise SerpError(f"Could not reach SerpApi: {exc}") from exc

        ms = int((time.time() - started) * 1000)
        try:
            data = resp.json()
        except ValueError:
            data = {}

        if resp.status_code in (401, 403):
            self._record(engine, purpose, query, "error", ms, False, 0, "invalid API key")
            raise SerpError("SerpApi rejected the API key. Check SERPAPI_KEY in your .env file.")
        if resp.status_code == 429:
            self._record(engine, purpose, query, "error", ms, False, 0, "rate limited / out of searches")
            raise SerpError("SerpApi says this account is rate limited or out of searches this month.")

        error = str(data.get("error", "")) if isinstance(data, dict) else ""
        if error:
            if any(h in error.lower() for h in _EMPTY_HINTS):
                self.searches_made += 1; self._bump_usage()
                self._record(engine, purpose, query, "empty", ms, False, 0, "no results")
                data = {"organic_results": [], "search_metadata": {"note": error}}
                path.write_text(json.dumps(data), encoding="utf-8")
                return data
            self._record(engine, purpose, query, "error", ms, False, 0, error[:120])
            raise SerpError(f"SerpApi error for {ENGINE_LABELS.get(engine, engine)}: {error}")

        self.searches_made += 1; self._bump_usage()
        if isinstance(data, dict):
            data.get("search_parameters", {}).pop("api_key", None)
        path.write_text(json.dumps(data), encoding="utf-8")
        n = count_results(data)
        self._record(engine, purpose, query, "ok" if n else "empty", ms, False, n)
        return data

class DemoSerpClient(_BaseClient):
    def __init__(self, responses=None):
        super().__init__()
        self.responses = responses or {}

    @staticmethod
    def _fake_latency(seed: str) -> int:
        h = int(hashlib.md5(seed.encode()).hexdigest()[:6], 16)
        return 420 + h % 900

    def search(self, engine, purpose, **params):
        label = params.pop("label", "")
        query = label or str(params.get("q", ""))
        data = self.responses.get(f"{engine}:{purpose}")
        ms = self._fake_latency(f"{engine}{query}")
        if data is None:
            self._record(engine, purpose, query, "empty", ms, False, 0, "no recorded data for this query")
            return {}
        self.searches_made += 1
        n = count_results(data)
        self._record(engine, purpose, query, "ok" if n else "empty", ms, False, n)
        return data

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
