"""Convert discovered workshops to YAML format and write proposed additions."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import yaml
from dateutil import parser as date_parser

from .agent import DiscoveredWorkshop


def to_yaml_block(w: DiscoveredWorkshop, parent_conference: str, year: int) -> dict:
    """Convert a DiscoveredWorkshop to the YAML schema used by workshops.yaml."""
    slug = (w.acronym or w.name).lower()
    slug = "".join(c for c in slug if c.isalnum() or c == "_")[:30]
    venue_id = f"{slug}_{parent_conference}"

    deadlines = []
    if w.paper_deadline:
        try:
            dt = date_parser.parse(w.paper_deadline)
            deadlines.append({
                "stage": "paper",
                "deadline": dt.strftime("%Y-%m-%d %H:%M:%S"),
                "timezone": w.paper_deadline_tz or "AoE",
            })
        except Exception:
            pass

    return {
        "id": venue_id,
        "name": w.acronym or w.name[:20],
        "full_name": w.full_name,
        "acronym": w.acronym,
        "parent_conference": parent_conference,
        "year": year,
        "url": w.url or "",
        "location": "",
        "start_date": "",
        "end_date": "",
        "tier": "workshop",
        "description": w.description or "",
        "submission_url": w.submission_url or "",
        "format_notes": w.format_notes or "",
        "topics": w.topics or [],
        "deadlines": deadlines,
        "_discovered_at": datetime.utcnow().isoformat() + "Z",
    }


def write_proposed_additions(
    discoveries: dict[str, list[DiscoveredWorkshop]],
    existing_workshops_yaml: Path,
    out_path: Path,
) -> int:
    """Write a YAML file of proposed new workshop entries (skipping duplicates)."""
    existing_ids: set[str] = set()
    if existing_workshops_yaml.exists():
        with open(existing_workshops_yaml) as f:
            data = yaml.safe_load(f) or {}
        existing_ids = {w["id"] for w in (data.get("workshops") or []) if "id" in w}

    new_blocks: list[dict] = []
    for parent, ws_list in discoveries.items():
        # Derive year from parent_id like "neurips2026"
        year = 2026
        for c in reversed(parent):
            if not c.isdigit():
                idx = parent.find(c) + 1
                try:
                    year = int(parent[idx:])
                except Exception:
                    pass
                break
        for w in ws_list:
            block = to_yaml_block(w, parent_conference=parent, year=year)
            if block["id"] in existing_ids:
                continue
            existing_ids.add(block["id"])
            new_blocks.append(block)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        yaml.safe_dump(
            {"proposed_workshops": new_blocks},
            f,
            sort_keys=False,
            allow_unicode=True,
        )
    return len(new_blocks)
