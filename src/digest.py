"""Builds per-subscriber digest messages with rich venue detail."""
from __future__ import annotations

from datetime import datetime, timezone, timedelta

from .data import Venue, Deadline, filter_venues
from . import subscribers as subs


NOTIFY_WINDOWS = [30, 14, 7, 3, 1]


def _format_relative(when_utc: datetime, now_utc: datetime) -> str:
    delta = when_utc - now_utc
    days = delta.days
    if days == 0:
        hours = max(0, delta.seconds // 3600)
        return f"in {hours}h"
    if days == 1:
        return "tomorrow"
    if days < 7:
        return f"in {days}d"
    if days < 30:
        return f"in {days // 7}w"
    return f"in {days // 30}mo"


STAGE_EMOJI = {
    "abstract": "📝", "paper": "📄", "supplementary": "📎",
    "camera_ready": "✨", "rebuttal": "💬", "notification": "📬",
    "registration": "🎫", "travel_grant": "✈️", "workshops_deadline": "🔬",
}


def _format_venue_block(venue: Venue, d: Deadline, user_tz: str, now_utc: datetime) -> str:
    """Multi-line block for one (venue, deadline). Richer than v1."""
    local = d.in_tz(user_tz)
    when_str = local.strftime("%Y-%m-%d %H:%M %Z")
    rel = _format_relative(d.when, now_utc)
    workshop_tag = "🔬 " if venue.is_workshop else "🎓 "

    name = venue.name
    if venue.is_workshop and venue.parent_conference:
        parent = venue.parent_conference.replace(str(venue.year), "").upper()
        name = f"{venue.name} @ {parent}"

    stage_emoji = STAGE_EMOJI.get(d.stage, "•")
    lines = [f"{workshop_tag}*{name}* {stage_emoji} _{d.stage}_ — {when_str} ({rel})"]

    if d.note:
        lines.append(f"   📌 _{d.note}_")

    # Description (scope)
    if venue.description:
        desc = venue.description.strip().replace("\n", " ")
        if len(desc) > 200:
            desc = desc[:197] + "..."
        lines.append(f"   📖 {desc}")

    # Stats line: ranking + acceptance rate + h-index
    stats = []
    if venue.ranking:
        stats.append(f"🏆 {venue.ranking}")
    if venue.acceptance_rate:
        stats.append(f"✅ accept: {venue.acceptance_rate}")
    if venue.h_index:
        stats.append(f"📊 h5={venue.h_index}")
    if venue.location:
        stats.append(f"📍 {venue.location}")
    if stats:
        lines.append("   " + " · ".join(stats))

    # Format notes
    if venue.format_notes:
        notes = venue.format_notes.strip().replace("\n", " ")
        if len(notes) > 150:
            notes = notes[:147] + "..."
        lines.append(f"   ⚙️ {notes}")

    # Links
    if venue.submission_url:
        lines.append(f"   ↗ Submit: {venue.submission_url}")
    if venue.url:
        lines.append(f"   🔗 {venue.url}")

    return "\n".join(lines)


def build_subscriber_digest(
    sub: dict,
    venues: list[Venue],
    notified: dict,
    now_utc: datetime | None = None,
    force: bool = False,
) -> tuple[str, list[tuple[str, str]]]:
    """Build a digest for one subscriber.

    Filter is the OR of: topics ∪ keywords ∪ venue_ids.
    Returns (message_text, list of (venue_id, stage) pairs to mark notified).
    """
    now_utc = now_utc or datetime.now(timezone.utc)
    handle = sub["handle"]
    user_tz = sub.get("timezone", "Asia/Tokyo")
    topics = sub.get("topics") or []
    keywords = sub.get("keywords") or []
    venue_ids = sub.get("venues") or []
    days_ahead = int(sub.get("digest_days_ahead", 30))
    include_workshops = bool(sub.get("include_workshops", True))
    include_conferences = bool(sub.get("include_conferences", True))

    has_subscriptions = bool(topics or keywords or venue_ids)
    if not has_subscriptions and not force:
        return "", []

    matched = filter_venues(
        venues,
        topics=topics or None,
        keywords=keywords or None,
        venue_ids=venue_ids or None,
        include_workshops=include_workshops,
        include_conferences=include_conferences,
    )

    horizon = now_utc + timedelta(days=days_ahead)
    upcoming = []
    to_notify = []
    for v in matched:
        for d in v.deadlines:
            if not (now_utc < d.when <= horizon):
                continue
            if force:
                upcoming.append((v, d))
                continue
            if subs.was_notified(notified, handle, v.id, d.stage):
                continue
            days_left = (d.when - now_utc).days
            if 0 <= days_left <= max(NOTIFY_WINDOWS):
                upcoming.append((v, d))
                to_notify.append((v.id, d.stage))

    if not upcoming:
        return "", []

    upcoming.sort(key=lambda pair: pair[1].when)

    # Header includes filter summary so user knows what produced this
    filter_parts = []
    if topics:
        filter_parts.append(f"topics: {', '.join(topics[:4])}{'…' if len(topics) > 4 else ''}")
    if keywords:
        filter_parts.append(f"keywords: {', '.join(keywords[:4])}{'…' if len(keywords) > 4 else ''}")
    if venue_ids:
        filter_parts.append(f"venues: {len(venue_ids)} specific")
    filter_summary = " | ".join(filter_parts) if filter_parts else "all"

    lines = [
        "🔭 *AI Workshop Radar digest*",
        f"_{len(upcoming)} upcoming deadline(s) in the next {days_ahead}d_",
        f"_Filter: {filter_summary}_",
        "",
    ]
    for v, d in upcoming:
        lines.append(_format_venue_block(v, d, user_tz, now_utc))
        lines.append("")
    lines.append("_To change subscriptions, edit data/me.yaml in your fork._")

    return "\n".join(lines), to_notify
