"""Data layer: load YAML files, parse deadlines, handle timezones.

Venue schema (v2) now supports rich metadata:
  - description: 1-2 sentence scope of the workshop/conf
  - h_index: Google Scholar h5-index (for ranking signal)
  - acceptance_rate: e.g. "25%"
  - ranking: e.g. "CORE A*", "CCF-A", "Tier 1"
  - submission_url: direct link to the submission system (OpenReview/CMT/easychair)
  - format_notes: page limit, anonymity, template, etc.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable

import pytz
import yaml
from dateutil import parser as date_parser

AOE_TZ = timezone(timedelta(hours=-12))


@dataclass
class Deadline:
    stage: str
    when: datetime
    original_tz: str
    note: str = ""

    def in_tz(self, tz_name: str) -> datetime:
        tz = pytz.timezone(tz_name)
        return self.when.astimezone(tz)


@dataclass
class Venue:
    id: str
    name: str
    full_name: str
    year: int
    url: str
    location: str
    start_date: str
    end_date: str
    tier: str
    topics: list[str]
    deadlines: list[Deadline] = field(default_factory=list)
    parent_conference: str | None = None
    acronym: str | None = None
    is_workshop: bool = False
    # v2 richer fields
    description: str = ""
    h_index: int | None = None
    acceptance_rate: str = ""
    ranking: str = ""
    submission_url: str = ""
    format_notes: str = ""

    def next_deadline(self, now: datetime | None = None) -> Deadline | None:
        now = now or datetime.now(timezone.utc)
        upcoming = [d for d in self.deadlines if d.when > now]
        return min(upcoming, key=lambda d: d.when) if upcoming else None

    def deadlines_within(self, now: datetime, days: int) -> list[Deadline]:
        end = now + timedelta(days=days)
        return [d for d in self.deadlines if now < d.when <= end]

    def searchable_text(self) -> str:
        """Return all text fields concatenated, lowercased, for keyword matching."""
        parts = [
            self.name, self.full_name, self.acronym or "",
            self.description, self.location, self.ranking,
            " ".join(self.topics),
        ]
        for d in self.deadlines:
            parts.append(d.note)
        return " ".join(p for p in parts if p).lower()


def _parse_deadline(raw: dict) -> Deadline | None:
    try:
        tz_str = raw.get("timezone", "UTC")
        dt_str = raw["deadline"]
        naive = dt_str if isinstance(dt_str, datetime) else date_parser.parse(str(dt_str))

        if tz_str.upper() == "AOE":
            when = naive.replace(tzinfo=AOE_TZ).astimezone(timezone.utc)
        elif tz_str.upper().startswith("UTC"):
            try:
                offset = float(tz_str[3:] or "0")
            except ValueError:
                offset = 0
            tz = timezone(timedelta(hours=offset))
            when = naive.replace(tzinfo=tz).astimezone(timezone.utc)
        else:
            try:
                tz = pytz.timezone(tz_str)
                when = tz.localize(naive).astimezone(timezone.utc)
            except pytz.UnknownTimeZoneError:
                when = naive.replace(tzinfo=timezone.utc)

        return Deadline(
            stage=raw.get("stage", "paper"),
            when=when,
            original_tz=tz_str,
            note=raw.get("note", "") or "",
        )
    except Exception as e:
        print(f"[data] failed to parse deadline {raw}: {e}")
        return None


def _parse_venue(raw: dict, is_workshop: bool = False) -> Venue:
    deadlines = []
    for d in raw.get("deadlines", []) or []:
        parsed = _parse_deadline(d)
        if parsed:
            deadlines.append(parsed)

    return Venue(
        id=raw["id"],
        name=raw["name"],
        full_name=raw.get("full_name", raw["name"]),
        year=int(raw.get("year", 0)),
        url=raw.get("url", "") or "",
        location=raw.get("location", "") or "",
        start_date=str(raw.get("start_date", "")),
        end_date=str(raw.get("end_date", "")),
        tier=raw.get("tier", "B") or "B",
        topics=list(raw.get("topics", []) or []),
        deadlines=deadlines,
        parent_conference=raw.get("parent_conference"),
        acronym=raw.get("acronym"),
        is_workshop=is_workshop,
        description=raw.get("description", "") or "",
        h_index=raw.get("h_index"),
        acceptance_rate=raw.get("acceptance_rate", "") or "",
        ranking=raw.get("ranking", "") or "",
        submission_url=raw.get("submission_url", "") or "",
        format_notes=raw.get("format_notes", "") or "",
    )


def load_venues(data_dir: str | Path | None = None) -> list[Venue]:
    data_dir = Path(data_dir or os.environ.get("DATA_DIR", "./data"))
    venues: list[Venue] = []
    for filename, is_ws in [("conferences.yaml", False), ("workshops.yaml", True)]:
        f = data_dir / filename
        if not f.exists():
            continue
        with open(f, "r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
        key = "workshops" if is_ws else "conferences"
        for raw in data.get(key, []):
            venues.append(_parse_venue(raw, is_workshop=is_ws))
    return venues


def load_topics(data_dir: str | Path | None = None) -> list[dict]:
    data_dir = Path(data_dir or os.environ.get("DATA_DIR", "./data"))
    f = data_dir / "topics.yaml"
    if not f.exists():
        return []
    with open(f, "r", encoding="utf-8") as fh:
        return (yaml.safe_load(fh) or {}).get("topics", [])


def matches_keywords(venue: Venue, keywords: list[str]) -> bool:
    """Return True if ANY keyword (case-insensitive, word-boundary or substring) matches."""
    if not keywords:
        return False
    text = venue.searchable_text()
    for kw in keywords:
        kw = kw.strip().lower()
        if not kw:
            continue
        # Match phrases (multi-word keywords) as substrings; single words with word boundary
        if " " in kw or "-" in kw:
            if kw in text:
                return True
        else:
            if re.search(rf"\b{re.escape(kw)}\b", text):
                return True
    return False


def filter_venues(
    venues: Iterable[Venue],
    topics: list[str] | None = None,
    keywords: list[str] | None = None,
    venue_ids: list[str] | None = None,
    include_workshops: bool = True,
    include_conferences: bool = True,
    tiers: list[str] | None = None,
) -> list[Venue]:
    """Filter venues. A venue is included if ANY of these matches:
       - its id is in venue_ids
       - any of its topics is in `topics`
       - any keyword in `keywords` matches its searchable text
    """
    out = []
    for v in venues:
        if not include_workshops and v.is_workshop:
            continue
        if not include_conferences and not v.is_workshop:
            continue
        if tiers and v.tier not in tiers:
            continue
        if venue_ids and v.id in venue_ids:
            out.append(v); continue
        if topics and any(t in v.topics for t in topics):
            out.append(v); continue
        if keywords and matches_keywords(v, keywords):
            out.append(v); continue
        # If user has NO subscriptions at all, include everything
        if not topics and not venue_ids and not keywords:
            out.append(v); continue
    # dedupe
    seen = set()
    deduped = []
    for v in out:
        if v.id not in seen:
            seen.add(v.id)
            deduped.append(v)
    return deduped
