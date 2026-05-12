"""YAML-backed subscriber storage for the fork-and-self-host model.

PRIVACY MODEL — IMPORTANT:
  - data/me.yaml stores ONLY public-safe info: handle, timezone, topics, venues
  - Telegram chat_id and Slack webhook are NEVER stored in YAML files
  - They are read from env vars / GitHub Actions secrets at runtime
  - When you fork the repo, you set TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID
    (and optionally SLACK_WEBHOOK_URL) as repo secrets in YOUR fork
  - Your secrets stay encrypted, accessible only by workflows in your fork

For multi-user instances (you maintain digests for a group): use the
data/subscribers/*.yaml directory pattern. Per-user creds are looked up as
TELEGRAM_CHAT_ID_<HANDLE> / SLACK_WEBHOOK_URL_<HANDLE> in env.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

import yaml


def me_yaml_path() -> Path:
    return Path(os.environ.get("DATA_DIR", "./data")) / "me.yaml"


def subscribers_dir() -> Path:
    return Path(os.environ.get("DATA_DIR", "./data")) / "subscribers"


def notified_path() -> Path:
    return Path(os.environ.get("DATA_DIR", "./data")) / "notified.yaml"


def _normalize(data: dict, handle_fallback: str) -> dict:
    data.setdefault("handle", handle_fallback)
    data.setdefault("timezone", "Asia/Tokyo")
    data.setdefault("topics", [])
    data.setdefault("keywords", [])
    data.setdefault("venues", [])
    data.setdefault("include_workshops", True)
    data.setdefault("include_conferences", True)
    data.setdefault("digest_days_ahead", 30)
    return data


def load_all_subscribers() -> list[dict]:
    out: list[dict] = []

    # Primary: data/me.yaml (single-user fork mode)
    me = me_yaml_path()
    if me.exists():
        with open(me, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        data = _normalize(data, handle_fallback="me")
        chat_id_env = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
        slack_env = os.environ.get("SLACK_WEBHOOK_URL", "").strip()
        if chat_id_env:
            try:
                data["telegram_chat_id"] = int(chat_id_env)
            except ValueError:
                pass
        if slack_env:
            data["slack_webhook"] = slack_env
        if data.get("telegram_chat_id") or data.get("slack_webhook"):
            out.append(data)
        else:
            print("[subs] data/me.yaml found but no TELEGRAM_CHAT_ID/SLACK_WEBHOOK_URL in env")

    # Secondary: data/subscribers/*.yaml (multi-user maintainer mode)
    d = subscribers_dir()
    if d.exists():
        for f in sorted(d.glob("*.yaml")):
            if f.name.startswith("_"):
                continue
            try:
                with open(f, "r", encoding="utf-8") as fh:
                    data = yaml.safe_load(fh) or {}
                data = _normalize(data, handle_fallback=f.stem)
                handle_up = data["handle"].upper().replace("-", "_")
                env_chat = os.environ.get(f"TELEGRAM_CHAT_ID_{handle_up}", "").strip()
                env_slack = os.environ.get(f"SLACK_WEBHOOK_URL_{handle_up}", "").strip()
                if env_chat:
                    try:
                        data["telegram_chat_id"] = int(env_chat)
                    except ValueError:
                        pass
                if env_slack:
                    data["slack_webhook"] = env_slack
                if data.get("telegram_chat_id") or data.get("slack_webhook"):
                    out.append(data)
            except Exception as e:
                print(f"[subs] failed to load {f}: {e}")

    return out


def load_notified() -> dict:
    p = notified_path()
    if not p.exists():
        return {}
    try:
        with open(p, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


def save_notified(data: dict) -> None:
    p = notified_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=True, allow_unicode=True)


def was_notified(notified: dict, handle: str, venue_id: str, stage: str) -> bool:
    return f"{venue_id}:{stage}" in (notified.get(handle, {}) or {})


def mark_notified(notified: dict, handle: str, venue_id: str, stage: str) -> None:
    notified.setdefault(handle, {})[f"{venue_id}:{stage}"] = datetime.now(timezone.utc).isoformat()
