# 🔭 AI Workshop Radar

> Personalized deadline notifications for top-tier AI conferences **and workshops**. **Zero servers** — runs entirely on GitHub Actions. Telegram + Slack delivery. MIT licensed.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Daily digest](https://img.shields.io/badge/runs%20on-GitHub%20Actions-blue)](https://github.com/features/actions)

## Why?

Every existing AI deadline tracker (aideadlines.org, ccfddl.com, mldeadlines.com, WikiCFP) has the same gaps: no real notifications, no workshop coverage, no personalization, stale data, NY-timezone bias. Full gap analysis in [docs/MOTIVATION.md](docs/MOTIVATION.md).

This project fixes those gaps **using only free GitHub infrastructure**. No server. No Heroku. No fly.io. Nothing to keep alive.

## How it works (zero servers)

```
       ┌─────────────────────────────────────────┐
       │  Your fork of this repo                 │
       │  ┌───────────────────────────────────┐  │
       │  │ data/me.yaml (your prefs, public) │  │
       │  │ Repo Secrets (your chat ID, etc.) │  │
       │  └───────────────────────────────────┘  │
       └──────────────────┬──────────────────────┘
                          │
            ┌─────────────┼──────────────┐
            ▼             ▼              ▼
     ┌──────────┐  ┌──────────┐   ┌────────────┐
     │  Daily   │  │ Weekly   │   │  Manual    │
     │  digest  │  │ discovery│   │  trigger   │
     │  (cron)  │  │  agent   │   │            │
     └────┬─────┘  └────┬─────┘   └─────┬──────┘
          │             │               │
          ▼             ▼               ▼
   ┌──────────────────────────────────────────┐
   │   Telegram / Slack messages → you        │
   └──────────────────────────────────────────┘
```

**The deal:** GitHub Actions can't run a real-time chat bot (no long-running processes on free tier). But it can run cron jobs perfectly. So instead of a bot you talk to, you **edit a YAML file in your forked repo** to set your preferences, and the cron sends you notifications.

## 🚀 Quick start (5 minutes, no servers)

### 1. Fork this repo

Click the **Fork** button at the top right. You'll have your own copy at `github.com/<your-handle>/ai-workshop-radar`.

### 2. Get a Telegram bot token

- Message [@BotFather](https://t.me/botfather) on Telegram → `/newbot`
- Pick a name and `@username` → BotFather sends you a token

### 3. Get your Telegram chat ID

- Message [@userinfobot](https://t.me/userinfobot) on Telegram
- It immediately replies with your chat ID (an integer like `123456789`)
- **Also:** start a chat with your new bot from step 2 by sending it any message — this is required so the bot is "allowed" to message you back

### 4. Add secrets to your fork

In your forked repo: **Settings → Secrets and variables → Actions → New repository secret**

| Secret name | Value |
|---|---|
| `TELEGRAM_BOT_TOKEN` | The token from BotFather |
| `TELEGRAM_CHAT_ID` | Your chat ID from @userinfobot |
| `SLACK_WEBHOOK_URL` *(optional)* | A Slack [incoming webhook URL](https://api.slack.com/messaging/webhooks) |

### 5. Edit `data/me.yaml` with your preferences

```yaml
handle: me
timezone: Asia/Tokyo
topics:
  - ai_safety
  - multimodal
  - nlp
include_workshops: true
include_conferences: true
digest_days_ahead: 30
```

Commit the change to your fork.

### 6. Enable Actions in your fork

GitHub disables Actions on new forks by default. Go to the **Actions** tab → click **I understand my workflows, go ahead and enable them**.

### 7. Test it

Go to **Actions → Daily digest → Run workflow**. Within a minute you should get a Telegram message with your upcoming deadlines.

From then on it runs every day at 00:00 UTC (09:00 JST). Done.

## 📂 What's in this repo

```
ai-workshop-radar/
├── data/
│   ├── conferences.yaml       # NeurIPS, ICML, ACL, EMNLP, AAAI, CVPR, ...
│   ├── workshops.yaml         # workshops at those conferences (the killer feature)
│   ├── topics.yaml            # research-area taxonomy
│   ├── me.yaml                # YOUR preferences (you edit this in your fork)
│   └── notified.yaml          # auto-managed: dedup state for notifications
├── src/
│   ├── data.py                # YAML loader + timezone handling
│   ├── subscribers.py         # reads me.yaml + credentials from env
│   ├── digest.py              # builds digest messages
│   ├── slack.py               # Slack webhook sender
│   └── scraper/agent.py       # LLM-based workshop CFP discovery
├── scripts/
│   ├── send_digests.py        # called by daily-digest workflow
│   └── discover_workshops.py  # called by auto-discovery workflow
├── .github/workflows/
│   ├── daily-digest.yml       # cron: send digest every 24h
│   └── auto-discovery.yml     # cron: scrape new workshops, open PR
└── docs/                      # SETUP, ARCHITECTURE, CONTRIBUTING, MOTIVATION
```

## ✨ Features

- 📱 **Telegram + Slack delivery** — pick one or both
- 🗓️ **Multi-stage deadlines** — abstract / paper / supplementary / camera-ready / travel grant / registration
- 🏷️ **Topic taxonomy** — `ai_safety`, `multimodal`, `nlp`, `japan_local`, etc.
- 🌏 **Per-user timezone** — IANA names; default `Asia/Tokyo`
- 🤖 **Weekly auto-discovery** — Gemini-powered agent scrapes conference workshop pages, opens a PR with proposed new entries (you review + merge)
- 🇯🇵 **Japan-domestic venues** seeded — NLP-JP, JSAI, MIRU, IBIS, ANLP
- 🔬 **Workshops are first-class** — none of the major trackers cover them well
- 🔕 **Notification dedup** — each (venue, stage) only pings you once

## 💸 Cost

| Resource | Cost | Limit |
|---|---|---|
| GitHub Actions | $0 | 2000 min/month free for public repos |
| Telegram Bot API | $0 | None |
| Slack incoming webhooks | $0 | None |
| Gemini API (free tier) | $0 | 15 req/min, 1500 req/day — way more than weekly scrapes need |
| **Total** | **$0** | |

A typical run uses ~30 seconds of Actions time, so 60s/day × 30 days = 30 min/month. You'd have to run thousands of users in one repo to hit the limit.

## 🤝 Contributing

The data layer is YAML — open a PR to add a conference or workshop. See [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md).

## 📜 License

MIT — see [LICENSE](LICENSE).
