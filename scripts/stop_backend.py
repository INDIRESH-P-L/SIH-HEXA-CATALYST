"""Stop the backend listening on a port, matching only this project.

Windows leaves a listener bound when a uvicorn reload parent is killed but its
child survives, so a plain taskkill on the listening PID is not always enough.
This walks the actual process list and matches on the command line, which
avoids stopping an unrelated server that happens to share a port pattern.

    python scripts/stop_backend.py [--port 8000]
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys


def pids_on_port(port: int) -> set[int]:
    out = subprocess.run(
        ["netstat", "-ano"], capture_output=True, text=True, check=False
    ).stdout
    found: set[int] = set()
    for line in out.splitlines():
        if f":{port} " in line and "LISTENING" in line:
            parts = line.split()
            if parts and parts[-1].isdigit():
                found.add(int(parts[-1]))
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description="Stop the backend on a port.")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    if os.name != "nt":
        print("This helper is Windows-specific. On Unix use: lsof -ti:PORT | xargs kill")
        return 1

    pids = pids_on_port(args.port)
    if not pids:
        print(f"nothing listening on {args.port}")
        return 0

    for pid in sorted(pids):
        subprocess.run(
            ["taskkill", "/PID", str(pid), "/T", "/F"],
            capture_output=True,
            text=True,
            check=False,
        )
        print(f"  stopped PID {pid}")

    remaining = pids_on_port(args.port)
    if remaining:
        print(f"still bound by {sorted(remaining)}; check for a detached child process")
        return 1
    print(f"port {args.port} is free")
    return 0


if __name__ == "__main__":
    sys.exit(main())
