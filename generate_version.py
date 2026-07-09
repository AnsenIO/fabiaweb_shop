#!/usr/bin/env python3
"""Generate version.json from the current git commit.

Run this before starting the server so /health can report the deployed commit.
"""

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent
OUTPUT = BASE / "version.json"


def run(cmd: list[str]) -> str:
    return subprocess.run(
        cmd,
        cwd=BASE,
        capture_output=True,
        text=True,
        check=False,
    ).stdout.strip()


def main() -> None:
    commit = run(["git", "rev-parse", "HEAD"])
    if not commit:
        commit = "unknown"

    committed_at = run(["git", "log", "-1", "--format=%cI", commit])
    if not committed_at:
        committed_at = datetime.now(timezone.utc).isoformat()

    branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    if not branch:
        branch = "unknown"

    version = {
        "commit": commit,
        "committed_at": committed_at,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "branch": branch,
    }

    OUTPUT.write_text(json.dumps(version, indent=2) + "\n")
    print(f"Generated {OUTPUT}: {commit}")


if __name__ == "__main__":
    main()
