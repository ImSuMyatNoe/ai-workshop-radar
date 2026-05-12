# Contributing

## Adding a conference or workshop

YAML files in `data/`. Open a PR to add a venue.

## Full schema (v2)

```yaml
- id: neurips2026             # required, unique, lowercase + year
  name: NeurIPS               # required, short
  full_name: Conference on Neural Information Processing Systems
  year: 2026                  # required
  url: https://neurips.cc/...
  location: San Diego, USA
  start_date: 2026-12-01
  end_date: 2026-12-07
  tier: A*                    # A* | A | B | workshop

  # === Richer metadata (v2 fields, all OPTIONAL but recommended) ===
  description: >              # 1-2 sentences in your own words. Used for keyword matching too.
    The premier ML conference covering deep learning, optimization, generative
    models, neuroscience-inspired AI, RL, fairness, theory, and applications.
  h_index: 372                # Google Scholar h5-index — see https://scholar.google.com/citations?view_op=top_venues
  acceptance_rate: "26.1%"    # string, can include the % sign
  ranking: CORE A*, CCF-A     # any community ranking signal
  submission_url: https://openreview.net/group?id=NeurIPS.cc/2026/Conference
  format_notes: >             # page limit, anonymity, template, etc.
    9 pages excluding refs/appendix; LaTeX template required; double-blind;
    unlimited supplementary; checklist mandatory.

  topics: [ml_general, ai_safety, multimodal]   # IDs from data/topics.yaml
  deadlines:
    - stage: paper            # abstract|paper|supplementary|rebuttal|notification|
                              # camera_ready|travel_grant|registration|workshops_deadline
      deadline: "2026-05-22 23:59:59"
      timezone: AoE           # AoE | UTC[±N] | <IANA tz, e.g. Asia/Tokyo>
      note: "Mandatory abstract registration"

# For workshops, ALSO include:
  parent_conference: neurips2026
  acronym: SafeGenAI
```

## Timezone rules

- `AoE` = "Anywhere on Earth" = UTC-12. Standard for ML conferences.
- `UTC`, `UTC+9`, `UTC-8` work.
- IANA names work: `Asia/Tokyo`, `Europe/London`, etc.

## Why fill in the v2 fields

- **`description`** powers keyword matching. A workshop describing itself as "jailbreaking, red-teaming, adversarial evaluation" will surface for users whose keywords include any of those terms.
- **`h_index`**, **`acceptance_rate`**, **`ranking`** appear in user digests as a stats line — helps prioritize which deadlines actually matter.
- **`submission_url`** is the one-click action. If you only fill in one v2 field, fill in this.
- **`format_notes`** saves users from clicking through to find the page limit.

## Adding a topic

Edit `data/topics.yaml`. Topic IDs are referenced by user subscriptions:
- Don't rename existing IDs.
- New IDs: short, snake_case.

## Adding a keyword to your own subscription

You don't need to PR for this — edit `data/me.yaml` in your fork:

```yaml
keywords:
  - jailbreak
  - vision-language
  - low-resource
  - tokyo
```

Single words use word-boundary matching. Multi-word phrases (with space or hyphen) use substring matching. Case-insensitive.

## PR checklist

- [ ] YAML validates: `PYTHONPATH=. python -c "from src.data import load_venues; load_venues()"`
- [ ] No duplicate IDs
- [ ] Deadlines in the future (or marked with note)
- [ ] Topics referenced exist in `topics.yaml`
- [ ] If `submission_url` is set, it links to OpenReview/CMT/easychair, NOT the conference homepage
