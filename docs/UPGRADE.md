# Upgrading v1 → v2

## What's new in v2

| Feature | v1 | v2 |
|---|---|---|
| User filters | Topics + venue IDs | Topics + **keywords** + venue IDs |
| Per-venue detail | Name, deadline, URL | + description, h-index, acceptance rate, ranking, submission URL, format notes |
| Digest format | One line per entry | Multi-line block with full context |
| Filter summary in digest | ❌ | ✅ shows what produced this digest |
| Discovery agent prompt | Basic | Asks Gemini for description + submission_url + format_notes |

## Backward compatibility

✅ **Fully backward compatible.** All v2 fields are optional. v1 `me.yaml` files keep working — they just lack keyword matching.

## How to upgrade (your existing repo)

If you've already set up v1 on GitHub, here's the minimum to upgrade:

### Files to replace

```
src/data.py
src/digest.py
src/subscribers.py
src/scraper/agent.py
src/scraper/workshops.py
data/me.yaml          (your prefs file)
data/conferences.yaml (richer seed data)
data/workshops.yaml   (richer seed data)
docs/CONTRIBUTING.md
tests/test_data.py
```

Files unchanged from v1:
```
src/__init__.py
src/slack.py
src/scraper/__init__.py
scripts/*.py
.github/workflows/*.yml
data/topics.yaml
README.md (slight tweaks)
LICENSE
requirements.txt
```

### From your local clone

```bash
cd ~/Downloads/ai-workshop-radar-gh   # or wherever your fork lives
# Replace the v2 files (drag and drop, or git apply a patch)
git add .
git commit -m "Upgrade to v2: keywords, rich venue metadata"
git push
```

Then go to **Actions → Daily digest → Run workflow** to see the new format immediately.

## Trying out keywords

Edit `data/me.yaml` and add a `keywords:` block:

```yaml
keywords:
  - vision-language
  - red teaming
  - jailbreak
  - multilingual
  - tokyo
  - japanese
```

Rules:
- Case-insensitive
- Single words match on word boundaries (so `bias` won't match `unbiased`)
- Multi-word phrases (with space or hyphen) match as substrings
- Matched against: venue name, full name, acronym, description, location, ranking, topics, deadline notes

Push the change. Re-run the workflow. You'll see venues that match your keywords even if they don't match your topics.

## Hidden trick: subscribe by location

Since location text is included in keyword matching:

```yaml
keywords:
  - tokyo
  - kyoto
  - osaka
  - japan
  - virtual
```

Will surface all Japan-located venues plus any virtual/hybrid options.
