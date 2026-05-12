"""LLM-based discovery agent.

Strategy: feed conference workshop-listing pages (e.g. neurips.cc/Conferences/.../workshops)
to an LLM and ask it to extract structured workshop entries matching our YAML schema.

Falls back to plain BeautifulSoup parsing if no LLM key is configured — slower
to bootstrap but still works as a starting point.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Iterable

import requests
from bs4 import BeautifulSoup


EXTRACTION_PROMPT = """You are extracting AI workshop call-for-papers info from a webpage.

For each workshop announced on this page, output a JSON object with these keys:
  - name: short workshop name (e.g. "SafeGenAI")
  - full_name: full title
  - acronym: short acronym if any
  - url: URL of the workshop's own page (NOT the parent conference)
  - paper_deadline: ISO-8601 datetime if visible, else null
  - paper_deadline_tz: e.g. "AoE", "UTC", "Asia/Tokyo", else null
  - description: 1-2 sentence scope of the workshop in your own words, or null
  - submission_url: link to OpenReview/CMT/easychair submission, else null
  - format_notes: page limit, anonymity, template (free text), else null
  - topics: zero or more of: ai_safety, multimodal, nlp, cv, ml_general, rl,
            agents, robotics, ai_ethics, interpretability, evaluation,
            low_resource, speech, hci_ai

Return ONLY a JSON array. If nothing is found, return [].

Page content:
---
{content}
---
"""


@dataclass
class DiscoveredWorkshop:
    name: str
    full_name: str
    acronym: str | None
    url: str | None
    paper_deadline: str | None
    paper_deadline_tz: str | None
    topics: list[str]
    description: str | None = None
    submission_url: str | None = None
    format_notes: str | None = None


def _fetch(url: str, timeout: int = 20) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; AIWorkshopRadar/0.1; +https://github.com/)"
    }
    r = requests.get(url, headers=headers, timeout=timeout)
    r.raise_for_status()
    return r.text


def _strip_html(html: str, max_chars: int = 40000) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for s in soup(["script", "style", "noscript"]):
        s.decompose()
    text = re.sub(r"\n{3,}", "\n\n", soup.get_text("\n"))
    return text[:max_chars]


def extract_with_gemini(content: str, api_key: str) -> list[DiscoveredWorkshop]:
    """Use Gemini's free tier (gemini-2.0-flash-exp or gemini-2.5-flash)."""
    try:
        import google.generativeai as genai
    except ImportError:
        print("[agent] google-generativeai not installed, skipping LLM")
        return []

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")
    prompt = EXTRACTION_PROMPT.format(content=content[:35000])
    try:
        resp = model.generate_content(prompt)
        raw = resp.text or ""
    except Exception as e:
        print(f"[agent] Gemini error: {e}")
        return []

    # Strip markdown code fences if present
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?", "", raw)
        raw = re.sub(r"```$", "", raw).strip()

    try:
        items = json.loads(raw)
    except Exception:
        # try to find a JSON array inside
        m = re.search(r"\[.*\]", raw, re.DOTALL)
        if not m:
            return []
        try:
            items = json.loads(m.group(0))
        except Exception:
            return []

    out = []
    for it in items:
        if not isinstance(it, dict) or not it.get("name"):
            continue
        out.append(DiscoveredWorkshop(
            name=str(it.get("name", "")).strip(),
            full_name=str(it.get("full_name") or it.get("name", "")).strip(),
            acronym=it.get("acronym") or None,
            url=it.get("url") or None,
            paper_deadline=it.get("paper_deadline") or None,
            paper_deadline_tz=it.get("paper_deadline_tz") or None,
            topics=list(it.get("topics") or []),
            description=it.get("description") or None,
            submission_url=it.get("submission_url") or None,
            format_notes=it.get("format_notes") or None,
        ))
    return out


def extract_with_bs4(content: str, base_url: str = "") -> list[DiscoveredWorkshop]:
    """Naive fallback: pull links that look like workshops."""
    out: list[DiscoveredWorkshop] = []
    soup = BeautifulSoup(content, "html.parser")
    for a in soup.find_all("a", href=True):
        text = a.get_text(strip=True)
        href = a["href"]
        if not text or len(text) > 200:
            continue
        # Heuristic: anchor text mentions "workshop"
        if re.search(r"\bworkshop\b", text, re.IGNORECASE):
            out.append(DiscoveredWorkshop(
                name=text[:60],
                full_name=text,
                acronym=None,
                url=href if href.startswith("http") else None,
                paper_deadline=None,
                paper_deadline_tz=None,
                topics=[],
            ))
    return out


def discover_from_url(url: str, conference_id: str | None = None) -> list[DiscoveredWorkshop]:
    """Discover workshops from a single conference workshop-listing URL."""
    print(f"[agent] fetching {url}")
    try:
        html = _fetch(url)
    except Exception as e:
        print(f"[agent] fetch failed: {e}")
        return []

    text = _strip_html(html)
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if api_key:
        results = extract_with_gemini(text, api_key)
        if results:
            print(f"[agent] Gemini returned {len(results)} workshops")
            return results
        print("[agent] Gemini returned nothing, falling back to BS4")
    return extract_with_bs4(html, base_url=url)


# Conference workshop-listing URLs to scrape weekly.
# Add more as new conferences open their workshop calls.
WORKSHOP_LISTING_URLS = [
    # (url, parent_conference_id)
    ("https://neurips.cc/Conferences/2026/CallForWorkshops", "neurips2026"),
    ("https://icml.cc/Conferences/2026/CallForWorkshops", "icml2026"),
    ("https://2026.aclweb.org/calls/workshops/", "acl2026"),
    ("https://2026.emnlp.org/calls/workshops/", "emnlp2026"),
    ("https://cvpr.thecvf.com/Conferences/2026", "cvpr2026"),
    ("https://aaai.org/conference/aaai/aaai-26/workshop-list/", "aaai2026"),
]


def discover_all() -> dict[str, list[DiscoveredWorkshop]]:
    """Run discovery across all configured conference workshop pages."""
    out: dict[str, list[DiscoveredWorkshop]] = {}
    for url, parent in WORKSHOP_LISTING_URLS:
        try:
            out[parent] = discover_from_url(url, conference_id=parent)
        except Exception as e:
            print(f"[agent] error on {url}: {e}")
            out[parent] = []
    return out
