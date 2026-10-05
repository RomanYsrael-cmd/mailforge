#!/usr/bin/env python3
"""Reapply the idempotent Phase 2 Stalwart configuration to a running lab."""

from __future__ import annotations

import sys

from lab import provision
from lab_common import RUNTIME


def main() -> int:
    if not (RUNTIME / "secrets.json").is_file():
        print("Run python scripts/lab.py up before reprovisioning the lab.", file=sys.stderr)
        return 1
    try:
        provision(recovery=False)
    except Exception as exc:
        print(f"Stalwart lab provisioning failed: {exc}", file=sys.stderr)
        return 1
    print("Reapplied the fixture-derived Stalwart configuration.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
