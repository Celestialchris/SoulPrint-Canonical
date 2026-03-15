from __future__ import annotations
import os, threading, webbrowser
from src.app import create_app

def _should_open_browser() -> bool:
    raw = os.getenv("SOULPRINT_OPEN_BROWSER", "1").strip().lower()
    return raw not in {"0", "false", "no", "off"}

def main() -> None:
    app = create_app()
    host = os.getenv("SOULPRINT_HOST", "127.0.0.1")
    port = int(os.getenv("SOULPRINT_PORT", "5678"))
    url = f"http://{host}:{port}"
    if _should_open_browser():
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    app.run(host=host, port=port, debug=False)

if __name__ == "__main__":
    main()
