from __future__ import annotations
import logging
from typing import Any
from flask import Flask, jsonify, request, send_from_directory
from .config import Config
from .demo_data import SAMPLE_INDEX, public_samples
from .engine import run_check
from .llm import make_explainer
from .serp import DemoSerpClient, LiveSerpClient, SerpError

log = logging.getLogger("trustlens")

def create_app() -> Flask:
    app = Flask(__name__, static_folder=str(Config.FRONTEND_DIR), static_url_path="")
    app.config["JSON_SORT_KEYS"] = False

    def live_client():
        return LiveSerpClient(Config.SERPAPI_KEY, Config.CACHE_DIR, Config.CACHE_HOURS, Config.DAILY_SEARCH_LIMIT,
                              Config.GL, Config.HL, Config.GOOGLE_DOMAIN)

    @app.get("/")
    def index():
        return send_from_directory(Config.FRONTEND_DIR, "index.html")

    @app.get("/api/health")
    def health():
        used = live_client().searches_today() if Config.live_available() else 0
        return jsonify({"ok": True, "mode": "live" if Config.live_available() else "demo",
                        "live_available": Config.live_available(), "key_configured": bool(Config.SERPAPI_KEY),
                        "explainer": bool(Config.ANTHROPIC_API_KEY), "searches_today": used,
                        "daily_limit": Config.DAILY_SEARCH_LIMIT})

    @app.get("/api/samples")
    def samples():
        return jsonify(public_samples())

    @app.post("/api/analyze")
    def analyze():
        body: dict[str, Any] = request.get_json(silent=True) or {}
        mode = str(body.get("mode", ""))
        inputs = body.get("inputs") or {}
        sample_id = body.get("sample_id")
        want_demo = bool(body.get("demo")) or not Config.live_available()
        try:
            if want_demo:
                sample = SAMPLE_INDEX.get(sample_id) if sample_id else None
                client: Any = DemoSerpClient(sample["responses"] if sample else None)
                report = run_check(mode, inputs, client, source="demo", sample_id=sample_id)
            else:
                explainer = make_explainer(Config.ANTHROPIC_API_KEY, Config.ANTHROPIC_MODEL) if Config.ANTHROPIC_API_KEY else None
                report = run_check(mode, inputs, live_client(), source="live", explainer=explainer)
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400
        except SerpError as exc:
            log.warning("SerpApi error: %s", exc)
            return jsonify({"error": str(exc)}), 502
        except Exception:
            log.exception("analysis failed")
            return jsonify({"error": "Something went wrong while running the check. Try again."}), 500
        return jsonify(report)

    return app
