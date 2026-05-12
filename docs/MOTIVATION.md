# Motivation: why another deadline tracker?

## The existing landscape

| Tool | Strength | Gap |
|---|---|---|
| [huggingface/ai-deadlines](https://github.com/huggingface/ai-deadlines) (aideadlines.org) | Maintained fork, clean UI, top-tier focus | No notifications, no workshops, manual PR updates, NY timezone default |
| [ccfddl/ccf-deadlines](https://github.com/ccfddl/ccf-deadlines) (ccfddl.com) | Most comprehensive (8.8k stars), Python CLI, WeChat applet | No email/push, workshop coverage thin, Chinese-language UX |
| [aideadlin.es](https://aideadlin.es) (original paperswithcode) | Originally THE deadline tracker | Stale since 2025, community moved away |
| [mldeadlines.com](https://mldeadlines.com), [conferencedeadlines.com](https://conferencedeadlines.com), [trybibby.com](https://trybibby.com) | Variations of the static-website pattern | No notifications |
| [WikiCFP](http://www.wikicfp.com) | HAS email alerts | Mixes legit + predatory venues, generic keyword matching, very high noise |
| [aiconftracker.com](https://www.aiconftracker.com/) | Tries to predict deadlines | Uses "typical historical patterns" — unreliable |

## The consistent gaps

1. **No personalized notifications.** Static websites force you to remember to
   visit them. WikiCFP has email but no quality filter.
2. **Workshop coverage is awful.** Every tracker prioritizes main conferences.
   But workshops have shorter, less-publicized deadlines — and they're where
   early-career researchers actually publish first.
3. **No multi-stage tracking.** Abstract → paper → supplementary → camera-ready
   → travel grant → registration. Trackers show one date.
4. **Manual maintenance → stale data.** PR-based updates are slow.
5. **No personalization by topic.** Show me all 200 confs; I care about 15.
6. **Timezone bias** (America/New_York default). Painful for Asia.
7. **No ARR cycle tracking** for NLP venues.
8. **No Japan/Asia-Pacific venue coverage** (NLP-JP, JSAI, MIRU, IBIS, ANLP).

## What this project does differently

| Gap | Our fix |
|---|---|
| 🔕 No notifications | Per-user Telegram / Slack digests, with notification dedup |
| 🧩 Workshops ignored | Workshops are first-class in `data/workshops.yaml` |
| 🤖 Manual updates | Weekly LLM-based auto-discovery agent (GitHub Actions cron) |
| 🏷️ Coarse filters | Topic taxonomy + per-venue subscription; pick exactly what you want |
| 🇺🇸 NY timezone | Per-user IANA timezone; default Asia/Tokyo |
| 📅 One deadline | Multi-stage tracking: abstract / paper / camera-ready / travel grant / … |
| 🇯🇵 Western-only | Japan-domestic venues seeded (NLP-JP, JSAI, MIRU, IBIS, ANLP) |
| 🌫️ Opaque (WikiCFP) | Public YAML data layer, MIT license, fork-friendly |

## Non-goals

- **Not a competitor to OpenReview.** We point users to deadline pages; submissions stay on OpenReview/Easychair/CMT.
- **Not a paper recommender.** Just deadlines. Paper recommendations are a different product.
- **Not a job board.** Just CFPs.
- **Not aiming for 100% coverage.** WikiCFP tries to list everything and ends up listing predatory venues. We focus on quality > quantity.
