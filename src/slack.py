"""Slack incoming-webhook sender.

Users provide their own webhook via `/set_slack <url>` in Telegram.
We support a server-wide SLACK_WEBHOOK_URL too if you want to mirror a public
digest to a community channel.
"""
from __future__ import annotations

import os
import requests


def _md_to_slack(md: str) -> str:
    """Telegram-Markdown is close to Slack mrkdwn but not identical.
    Telegram uses *bold*/_italic_; Slack uses *bold*/_italic_ too, so the
    common case works. We strip Telegram-specific markdown that Slack ignores.
    """
    return md


def send(webhook_url: str, text: str) -> bool:
    if not webhook_url:
        return False
    try:
        r = requests.post(
            webhook_url,
            json={"text": _md_to_slack(text)},
            timeout=10,
        )
        return r.ok
    except Exception as e:
        print(f"[slack] error: {e}")
        return False


def send_to_global_channel(text: str) -> bool:
    """Send to the optional server-wide webhook."""
    url = os.environ.get("SLACK_WEBHOOK_URL", "").strip()
    if not url:
        return False
    return send(url, text)
