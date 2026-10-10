from backend.app import create_app
from backend.config import Config

if __name__ == "__main__":
    mode = "LIVE (SerpApi key found)" if Config.live_available() else "DEMO (recorded data, no credits used)"
    print(f"\n  TrustLens running in {mode}\n  Open http://localhost:{Config.PORT}\n")
    create_app().run(host="127.0.0.1", port=Config.PORT, debug=False)
