# cc-knowledge

> A Claude Code skill that turns your AI conversations into a personal knowledge base — automatically.

Every time you close a Claude Code window, that conversation disappears from context. The insights, the Q&As, the mistakes you just made — gone. **cc-knowledge captures all of it**, organizes it into a structured vault, and makes it searchable in any Markdown editor.

---

## What you get

```
CC-Knowledge/
  session-recaps/       ← one file per valuable conversation
  concept-library/      ← one page per tool or concept, compounds over time
  methodology/          ← reusable principles extracted from your work
  engineering-insights/ ← technical gotchas and discoveries
  mistake-log/          ← mistakes logged so you don't repeat them
  projects/             ← per-project overviews
  open-source-library/  ← useful repos you've found
  qa-handbook/          ← Q&As organized by topic
  weekly-digest/        ← weekly summaries
  _system/              ← index, log, schema
```

Two ways knowledge gets in:

**`/o` — manual, takes 3 seconds.** Run it at the end of any conversation worth remembering. Claude reads the conversation, extracts what matters, and files it.

**Auto-ingest — runs every morning at 9am.** Scans your Claude Code conversation history, decides what's worth documenting, and writes it while you sleep. You close the window and move on. It handles the rest.

---

## Install

**Requirements:** macOS, Python 3.9+, Node.js, Claude Code, Anthropic API key ([get one](https://console.anthropic.com))

```bash
git clone https://github.com/YoriHan/cc-knowledge ~/.claude/skills/cc-knowledge
cd ~/.claude/skills/cc-knowledge
./setup
```

Three questions:

```
What language do you want for your notes? (e.g. English, 中文, Español, 日本語)
→ English

Where should your knowledge base live? [~/Documents/CC-Knowledge]
→ (press Enter for default)

Your Anthropic API key (sk-ant-...):
→ sk-ant-...
```

That's it. Setup will:
- Create your vault with the full directory structure
- Configure MCP so Claude can read and write your vault
- Translate all scaffold files to your chosen language (if not English)
- Register a launchd job to run auto-ingest at 9am daily

**After setup:** restart Claude Code once to pick up the new MCP server.

---

## Usage

### `/o` — save this conversation

Type `/o` at the end of any conversation worth keeping. Claude will:

1. Read `_system/index.md` to understand your existing vault
2. Write a session recap with: what was done, methodology, what went well, what to improve, reusable principles, engineering insights, Q&As
3. Update or create concept library pages for tools/concepts that came up
4. Sync Q&As to the right qa-handbook file
5. Update the index and log

### Auto-ingest — runs while you sleep

Every morning at 9am, `daily_ingest.py` processes conversations from the past day:

- Skips trivial conversations (< 4 user messages, or conversations Claude judges not worth documenting)
- Waits 60 minutes after last activity before processing (conversation might still be ongoing)
- Generates session recaps and Q&As in your configured language

Check what ran:
```bash
tail -f ~/.cc-knowledge/ingest.log
```

### Manual commands

```bash
# Preview what would happen, without writing anything
python3 ~/.cc-knowledge/daily_ingest.py --dry-run

# Force reprocess one conversation (pass the UUID from ~/.claude/projects/)
python3 ~/.cc-knowledge/daily_ingest.py --force <uuid>

# Reprocess all conversations (ignores state)
python3 ~/.cc-knowledge/daily_ingest.py --all
```

---

## How the auto-ingest decides what to keep

Two-phase API call for each conversation:

**Phase 1 (claude-sonnet-4-6):** Is this worth documenting? Filters out: greetings, very short exchanges, conversations with no meaningful technical content.

**Phase 2 (claude-sonnet-4-6 + claude-haiku):** Generate the session recap in your language, extract Q&As.

You can override any decision with `--force`.

---

## Cost

| Usage | Est. cost |
|-------|-----------|
| Per conversation processed | $0.01–0.05 |
| Daily use (~5 conversations) | ~$0.10–0.25/day |
| Monthly | ~$3–7/month |

Models: `claude-sonnet-4-6` for recap generation, `claude-haiku-4-5-20251001` for Q&A extraction and translation.

---

## Config

`~/.cc-knowledge/config.json` — edit to change any setting without re-running setup:

```json
{
  "vault_path": "/Users/you/Documents/CC-Knowledge",
  "language": "English",
  "api_key": "sk-ant-..."
}
```

---

## Uninstall

```bash
# Stop the daily job
launchctl unload ~/Library/LaunchAgents/com.user.cc-knowledge.plist
rm ~/Library/LaunchAgents/com.user.cc-knowledge.plist

# Remove config and state
rm -rf ~/.cc-knowledge

# Remove the MCP entry: edit ~/.claude.json and delete the "cc-knowledge" key

# Optionally delete your vault (your notes — make sure you want to)
rm -rf ~/Documents/CC-Knowledge
```

---

## Platform support

macOS only in v1. The auto-ingest uses launchd for scheduling. Linux/Windows support (cron / Task Scheduler) is planned.

The `/o` command works on any platform — only the auto-ingest is macOS-specific.

---

## Why this exists

Claude Code conversations are ephemeral by design. The insights you gain, the patterns you notice, the mistakes you make — they exist only in the conversation window. This skill makes them persistent and searchable, compounding across every session you run.

The vault structure is designed around [Karpathy's LLM Wiki pattern](https://x.com/karpathy): same concept = one page, always update rather than create, let knowledge compound over time rather than proliferate into duplicates.
