from __future__ import annotations

import argparse
import datetime
import json
import os
import sqlite3
import sys
from pathlib import Path

from src.runtime import default_instance_dir

PROVIDERS = ["chatgpt", "claude", "gemini", "grok", "claude_code"]


def _default_db() -> Path:
    return default_instance_dir() / "soulprint.db"


def _cmd_serve(args: argparse.Namespace) -> None:
    if args.port is not None:
        os.environ["SOULPRINT_PORT"] = str(args.port)
    if args.host is not None:
        os.environ["SOULPRINT_HOST"] = args.host
    if args.no_browser:
        os.environ["SOULPRINT_OPEN_BROWSER"] = "0"
    from src.main import main as run_server
    run_server()


def _cmd_info(args: argparse.Namespace) -> None:
    db_path = Path(args.db) if args.db else _default_db()
    if not db_path.exists():
        print(
            f"Database not found at {db_path}. Run soulprint serve first to initialize.",
            file=sys.stderr,
        )
        sys.exit(1)

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        conv_count = conn.execute("SELECT COUNT(*) FROM imported_conversation").fetchone()[0]
        msg_count = conn.execute("SELECT COUNT(*) FROM imported_message").fetchone()[0]
        note_count = conn.execute("SELECT COUNT(*) FROM memory_entry").fetchone()[0]
        provider_rows = conn.execute(
            "SELECT source, COUNT(*) as cnt FROM imported_conversation GROUP BY source"
        ).fetchall()
        date_row = conn.execute(
            "SELECT MIN(created_at_unix), MAX(created_at_unix) FROM imported_conversation"
        ).fetchone()
    finally:
        conn.close()

    providers = {r["source"]: r["cnt"] for r in provider_rows}
    min_ts, max_ts = date_row[0], date_row[1]
    db_size = os.path.getsize(str(db_path))

    from src.intelligence.provider import is_llm_configured
    llm_ok = is_llm_configured()
    llm_provider = os.environ.get("SOULPRINT_LLM_PROVIDER")
    llm_base_url = os.environ.get("SOULPRINT_LLM_BASE_URL")
    llm_model = os.environ.get("SOULPRINT_LLM_MODEL")

    def _iso(ts: float | None) -> str | None:
        if ts is None:
            return None
        return datetime.datetime.utcfromtimestamp(ts).date().isoformat()

    if args.json:
        obj = {
            "db_path": str(db_path.resolve()),
            "conversations": conv_count,
            "messages": msg_count,
            "notes": note_count,
            "providers": providers,
            "date_range": {"min": _iso(min_ts), "max": _iso(max_ts)},
            "db_size_bytes": db_size,
            "intelligence": {
                "configured": llm_ok,
                "provider": llm_provider,
                "base_url": llm_base_url,
                "model": llm_model,
            },
        }
        print(json.dumps(obj, indent=2))
        return

    print(f"\nSoulPrint — {db_path.resolve()}\n")
    print(f"  Conversations: {conv_count:>10,}")
    print(f"  Messages:      {msg_count:>10,}")
    print(f"  Notes:         {note_count:>10,}")
    if providers:
        print("  Providers:")
        for p in PROVIDERS:
            if p in providers:
                print(f"    {p}: {providers[p]:>8,}")
    d_min, d_max = _iso(min_ts), _iso(max_ts)
    date_str = f"{d_min} to {d_max}" if d_min else "none"
    print(f"  Date range: {date_str}")
    print(f"  Database size: {db_size / 1_048_576:.1f} MB")
    if llm_ok and llm_base_url and llm_model:
        print(f"  Intelligence: configured ({llm_provider} @ {llm_base_url}, model: {llm_model})")
    elif llm_ok:
        print("  Intelligence: configured")
    else:
        print("  Intelligence: not configured")


def _cmd_mcp_config(_args: argparse.Namespace) -> None:
    import shutil

    # P1: honor SOULPRINT_DB, matching src/mcp_server.py precedence.
    env_db = os.environ.get("SOULPRINT_DB")
    if env_db:
        db_path = str(Path(env_db).resolve())
    else:
        db_path = str(_default_db().resolve())

    # P2: prefer the installed soulprint-mcp entry point so the pasted config
    # does not depend on whichever `python` happens to be first on PATH.
    mcp_cmd = shutil.which("soulprint-mcp")
    if mcp_cmd:
        command = mcp_cmd
        cmd_args: list[str] = []
    else:
        command = sys.executable
        cmd_args = ["-m", "src.mcp_server"]

    obj = {
        "mcpServers": {
            "soulprint": {
                "command": command,
                "args": cmd_args,
                "env": {"SOULPRINT_DB": db_path},
            }
        }
    }
    print(json.dumps(obj, indent=2))


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="soulprint",
        description="SoulPrint — local-first AI memory continuity system",
    )
    sub = parser.add_subparsers(dest="command")

    serve_p = sub.add_parser("serve", help="Start the SoulPrint web server")
    serve_p.add_argument("--port", type=int, default=None)
    serve_p.add_argument("--host", default=None)
    serve_p.add_argument("--no-browser", action="store_true")

    info_p = sub.add_parser("info", help="Show archive statistics")
    info_p.add_argument("--json", action="store_true")
    info_p.add_argument("--db", default=None, metavar="PATH")

    sub.add_parser("mcp-config", help="Print a ready-to-paste .mcp.json block")

    args = parser.parse_args(argv)

    if args.command is None:
        from src.main import main as run_server
        run_server()
    elif args.command == "serve":
        _cmd_serve(args)
    elif args.command == "info":
        _cmd_info(args)
    elif args.command == "mcp-config":
        _cmd_mcp_config(args)
