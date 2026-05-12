"""Sanity tests for the v2 data + digest layers."""
from pathlib import Path
import os
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data import load_venues, load_topics, filter_venues, matches_keywords
from src import subscribers as subs
from src.digest import build_subscriber_digest


def test_load_venues_doesnt_crash():
    venues = load_venues(Path("./data"))
    assert len(venues) > 0


def test_load_topics():
    topics = load_topics(Path("./data"))
    ids = {t["id"] for t in topics}
    assert {"ai_safety", "multimodal", "japan_local"}.issubset(ids)


def test_venue_ids_unique():
    venues = load_venues(Path("./data"))
    ids = [v.id for v in venues]
    assert len(ids) == len(set(ids))


def test_workshops_have_parents():
    venues = load_venues(Path("./data"))
    confs = {v.id for v in venues if not v.is_workshop}
    for v in venues:
        if v.is_workshop and v.parent_conference:
            assert v.parent_conference in confs


def test_topics_are_known():
    venues = load_venues(Path("./data"))
    topics = load_topics(Path("./data"))
    known = {t["id"] for t in topics}
    for v in venues:
        for t in v.topics:
            assert t in known, f"{v.id} has unknown topic {t}"


def test_keyword_match_single_word():
    venues = load_venues(Path("./data"))
    # SafeGenAI workshop description mentions "jailbreaking", "red-teaming"
    matched = [v for v in venues if matches_keywords(v, ["jailbreaking"])]
    assert len(matched) > 0, "expected at least one venue matching 'jailbreaking'"


def test_keyword_match_phrase():
    venues = load_venues(Path("./data"))
    matched = [v for v in venues if matches_keywords(v, ["vision-language"])]
    assert len(matched) > 0, "expected at least one venue matching 'vision-language'"


def test_keyword_OR_topic_OR_venue():
    venues = load_venues(Path("./data"))
    out_kw = filter_venues(venues, keywords=["jailbreaking"])
    out_topic = filter_venues(venues, topics=["ai_safety"])
    out_combined = filter_venues(venues, topics=["ai_safety"], keywords=["multilingual"])
    # combined should be superset of either alone
    assert len(out_combined) >= max(len(out_kw), len(out_topic))


def test_rich_fields_present():
    """At least the seeded venues have description/h_index/acceptance_rate populated."""
    venues = load_venues(Path("./data"))
    neurips = next((v for v in venues if v.id == "neurips2026"), None)
    assert neurips is not None
    assert neurips.description, "neurips2026 should have a description"
    assert neurips.h_index, "neurips2026 should have h_index"
    assert neurips.acceptance_rate, "neurips2026 should have acceptance_rate"
    assert neurips.submission_url, "neurips2026 should have submission_url"


def test_load_me_yaml_with_keywords():
    me = Path("./data/me.yaml")
    assert me.exists()
    import yaml
    with open(me) as f:
        data = yaml.safe_load(f)
    assert "keywords" in data, "me.yaml should have a keywords field"


def test_digest_with_keywords():
    """With keywords-only subscription, we should still get matched venues."""
    sub = {
        "handle": "test",
        "timezone": "Asia/Tokyo",
        "topics": [],
        "keywords": ["vision-language", "jailbreaking"],
        "venues": [],
        "include_workshops": True,
        "include_conferences": True,
        "digest_days_ahead": 365,  # wide horizon so it's deterministic
    }
    venues = load_venues()
    text, _ = build_subscriber_digest(sub, venues, {}, force=True)
    assert "AI Workshop Radar" in text
    # The filter summary should mention keywords
    assert "keywords" in text


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"✓ {name}")
    print("✅ all tests passed")
