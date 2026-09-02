"""Keep a paused-on-idle project awake.

A Supabase free project pauses after seven days with no API requests, which
would silently break a demonstration prepared a week in advance. This pings the
health endpoint so the clock resets.

    python scripts/keepalive.py
    python scripts/keepalive.py --url https://your-host/health/keepalive

Schedule it daily:

  Windows   schtasks /create /tn "SIP keepalive" /tr ^
              "C:\path\backend\.venv\Scripts\python.exe C:\path\scripts\keepalive.py" ^
              /sc daily /st 09:00
  Unix      0 9 * * *  /path/backend/.venv/bin/python /path/scripts/keepalive.py

The backend can also do it itself: set KEEPALIVE_ENABLED=true and it pings the
database on an interval from inside its own lifespan. That only helps while the
process is running, which is why this script exists as well.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

DEFAULT_URL = "http://127.0.0.1:8000/health/keepalive"


def main() -> int:
    parser = argparse.ArgumentParser(description="Ping the keep-alive endpoint.")
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--timeout", type=float, default=30.0)
    args = parser.parse_args()

    stamp = datetime.now(tz=timezone.utc).isoformat(timespec="seconds")
    try:
        with urllib.request.urlopen(args.url, timeout=args.timeout) as response:
            body = json.loads(response.read() or b"{}")
        print(
            f"{stamp}  ok  {args.url}  "
            f"db_roundtrip={body.get('database_roundtrip_ms', '?')}ms"
        )
        return 0
    except urllib.error.URLError as exc:
        print(f"{stamp}  FAILED  {args.url}  {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
