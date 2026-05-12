# Setup guide (GitHub-only deployment)

This project runs entirely on GitHub Actions. No server, no hosting cost, no maintenance.

## Setting up your fork

### 1. Fork the repo

Top right of GitHub → **Fork**. You'll get `github.com/<your-handle>/ai-workshop-radar`.

### 2. Create your Telegram bot

1. Message [@BotFather](https://t.me/botfather)
2. Send `/newbot`
3. Pick a display name (e.g. "My Deadline Radar")
4. Pick a `@username` ending in `bot` (must be unique globally)
5. BotFather sends you a token like `1234567:ABCdef...` — save it

### 3. Find your Telegram chat ID

1. Message [@userinfobot](https://t.me/userinfobot)
2. It replies with your chat ID — copy it
3. **Important:** also send any message to YOUR new bot first. Telegram requires the user to "open" the conversation before a bot can DM them. Just say "hi" to your bot.

### 4. Configure GitHub Actions secrets

In your forked repo: **Settings → Secrets and variables → Actions → New repository secret**

Required:
- `TELEGRAM_BOT_TOKEN` → token from BotFather
- `TELEGRAM_CHAT_ID` → your chat ID from @userinfobot

Optional:
- `SLACK_WEBHOOK_URL` → Slack incoming webhook for parallel delivery
- `GEMINI_API_KEY` → for the auto-discovery agent ([free key](https://aistudio.google.com/apikey))

### 5. Edit `data/me.yaml`

Open `data/me.yaml` in your fork (GitHub web UI is fine) and set:

```yaml
timezone: Asia/Tokyo
topics:
  - ai_safety
  - multimodal
  - nlp
include_workshops: true
include_conferences: true
digest_days_ahead: 30
```

Commit. (Pro tip: pick MORE topics than you think — you can always narrow later.)

### 6. Enable Actions

GitHub disables workflows on new forks for safety. Go to the **Actions** tab and click the green "I understand my workflows, go ahead and enable them" button.

### 7. Run the digest manually for testing

**Actions → Daily digest → Run workflow → Run workflow** (green button).

Within ~60 seconds you should get a Telegram message. If you don't:
- Check the workflow run logs (click on the failed run)
- Verify you started a conversation with your bot
- Verify TELEGRAM_CHAT_ID is correct (no spaces, no quotes)

### 8. Adjust the schedule

By default the digest runs at 00:00 UTC. To change it, edit `.github/workflows/daily-digest.yml`:

```yaml
on:
  schedule:
    - cron: "0 0 * * *"   # 00:00 UTC = 09:00 JST
```

[Cron expression generator](https://crontab.guru/) for picking times.

## Setting up auto-discovery (optional but recommended)

The discovery agent scrapes conference workshop pages weekly and opens a PR with new entries.

1. Get a Gemini API key: https://aistudio.google.com/apikey (free)
2. Add `GEMINI_API_KEY` to your fork's secrets
3. The workflow runs Sundays at 02:00 UTC by default
4. When it finds something, it opens a PR in your fork — review and merge

Without `GEMINI_API_KEY`, the agent falls back to naive HTML parsing. Works but produces lower-quality extractions.

## Multi-user mode

If you want to run digests for friends or your research group, the project supports it.

1. Create files in `data/subscribers/` — one per person, e.g. `data/subscribers/alice.yaml`:

```yaml
handle: alice
timezone: Europe/Vienna
topics:
  - nlp
  - low_resource
include_workshops: true
digest_days_ahead: 14
```

2. Add namespaced secrets in your fork (one set per person):
   - `TELEGRAM_CHAT_ID_ALICE`
   - `SLACK_WEBHOOK_URL_ALICE` (optional)

3. The script reads them automatically (uppercased handle with `_` separator).

Trade-off: you (the maintainer) are now responsible for everyone's chat IDs and webhooks as secrets. For larger groups, each member forking their own copy stays cleaner.

## Troubleshooting

**The workflow ran but I got nothing.**
- Did you actually send your bot a message first? Telegram requires it.
- Check the workflow logs for the line `[digest] me: sent (...)` or error.

**I get "TELEGRAM_BOT_TOKEN missing".**
- Secret name must be exactly `TELEGRAM_BOT_TOKEN` (case-sensitive).

**The digest is empty.**
- You haven't subscribed to any topics, OR
- No deadlines in your topics fall in the next 30 days, OR
- You've already been notified about everything (check `data/notified.yaml`).
- To re-test, delete `data/notified.yaml`, commit, and rerun.

**I want to receive digests more often than once a day.**
- Edit the cron in `.github/workflows/daily-digest.yml`. But note: GitHub charges Actions minutes against your free quota.
