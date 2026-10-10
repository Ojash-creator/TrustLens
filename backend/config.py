from __future__ import annotations
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

_load_dotenv(ROOT / ".env")

def _flag(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}

class Config:
    ROOT = ROOT
    FRONTEND_DIR = ROOT / "frontend"
    CACHE_DIR = ROOT / ".cache"
    SERPAPI_KEY = os.getenv("SERPAPI_KEY", "").strip()
    FORCE_DEMO = _flag("TRUSTLENS_DEMO")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()
    ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5").strip()
    DAILY_SEARCH_LIMIT = int(os.getenv("TRUSTLENS_DAILY_SEARCH_LIMIT", "40"))
    CACHE_HOURS = float(os.getenv("TRUSTLENS_CACHE_HOURS", "24"))
    PORT = int(os.getenv("PORT", "5000"))
    GL, HL, GOOGLE_DOMAIN = "in", "en", "google.co.in"

    @classmethod
    def live_available(cls) -> bool:
        return bool(cls.SERPAPI_KEY) and not cls.FORCE_DEMO
