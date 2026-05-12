"""Weekly auto-discovery: scrape conference workshop pages, write proposed
additions to data/proposed_workshops.yaml. The GH Action then opens a PR.
"""
from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv

from src.scraper.agent import discover_all
from src.scraper.workshops import write_proposed_additions


def main():
    load_dotenv()
    data_dir = Path("./data")
    existing = data_dir / "workshops.yaml"
    out = data_dir / "proposed_workshops.yaml"

    print("[discover] running workshop discovery agent…")
    results = discover_all()
    total = sum(len(v) for v in results.values())
    print(f"[discover] discovered {total} workshops across {len(results)} conferences")

    n_new = write_proposed_additions(results, existing, out)
    print(f"[discover] wrote {n_new} new (deduped) workshops to {out}")
    if n_new == 0:
        # exit code 78 = no-op for GH Actions (action can skip PR creation)
        sys.exit(0)


if __name__ == "__main__":
    main()
