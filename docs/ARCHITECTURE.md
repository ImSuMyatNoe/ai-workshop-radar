# Architecture

## The "GitHub-as-everything" model

Most apps need three layers: storage, scheduling, and message delivery. We get all three from GitHub for free:

| Layer | Hosted on | Cost |
|---|---|---|
| Code | GitHub repo | $0 |
| Data (conferences, workshops, prefs) | YAML in the repo | $0 |
| Scheduler | GitHub Actions cron | $0 |
| Secrets (chat ID, tokens) | GitHub Actions secrets | $0 |
| Notification dedup state | `data/notified.yaml` committed back by the workflow | $0 |
| Delivery | Telegram Bot API + Slack webhooks (both free) | $0 |
| Auto-discovery LLM | Gemini free tier (15 RPM / 1500 RPD) | $0 |

The total cost of running this for one person is **0 dollars and 0 cents**, indefinitely.

## Three workflows, three jobs

```
┌──────────────────────────────────────────────────────────────┐
│  data/conferences.yaml, workshops.yaml, topics.yaml, me.yaml │
└────────────────────────────┬─────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
 ┌──────────────┐    ┌────────────────┐    ┌──────────────────┐
 │  daily-      │    │  auto-         │    │  (Manual)        │
 │  digest.yml  │    │  discovery.yml │    │  workflow_       │
 │  cron daily  │    │  cron weekly   │    │  dispatch        │
 └──────┬───────┘    └────────┬───────┘    └────────┬─────────┘
        │                     │                     │
        ▼                     ▼                     ▼
  Read me.yaml +        Scrape conf URLs       Test on demand
  env secrets;          → Gemini extract
  build digest;         → PR with proposed
  POST Telegram;          additions
  POST Slack;
  commit notified.yaml
```

## Why YAML files instead of a database

- **Transparency.** Anyone can audit the data layer; this is your differentiator vs. WikiCFP's opacity.
- **Version control.** Every change to a conference deadline has a commit attached. "When did the EMNLP 2026 deadline move?" → `git blame`.
- **Forkability.** No DB to migrate when someone forks. Just copy the repo.
- **PR-able.** Community contributions are free.
- **State for free.** The notification-dedup file (`notified.yaml`) is just another YAML committed back at the end of each digest run.

## Why "fork and self-host" instead of one central instance

- **Privacy.** Your chat ID never leaves your fork's encrypted secrets.
- **No coordinator.** You don't have to trust me (or anyone) to keep a bot alive, manage spam, etc.
- **Survives if I disappear.** Forks keep working forever; just a `git pull` from upstream to get new conference data.
- **Customizable per-user.** Want a different schedule? Different format? Fork and tweak.

The cost: setup is a 5-minute one-time chore instead of "click subscribe." For researchers, that's fine.

## How notification dedup works

Without dedup, every daily digest would re-list the same NeurIPS abstract deadline for the next 30 days.

```python
NOTIFY_WINDOWS = [30, 14, 7, 3, 1]
```

For each (subscriber, venue, stage):
1. Skip if deadline is in the past or >30 days out.
2. Check `notified.yaml` — was this combo already dispatched?
3. If not, include in today's digest AND record it.

The workflow commits `notified.yaml` back to the repo after each run. So the next day's run sees the previous day's state.

If you want to re-receive a notification (e.g. you missed it), delete the relevant entry from `notified.yaml`, commit, and rerun the workflow manually.

## Limits

| Limit | Threshold | What happens |
|---|---|---|
| GitHub Actions minutes | 2000 min/month free for public repos | Way more than we need (~30 min/month per fork) |
| Telegram Bot API | No real limit for outgoing messages | Fine |
| Slack incoming webhooks | 1 message/sec per webhook | Fine for daily digest |
| Gemini free tier | 15 RPM / 1500 RPD | Way more than ~10 weekly scrapes |
| YAML file size | Practical limit ~10MB | We're at ~10KB |
