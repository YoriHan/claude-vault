# cc-knowledge

> A Claude Code skill that automatically turns your CC conversations into a searchable personal knowledge base.

## What you get

After one-line install:
- A structured Obsidian/Markdown vault (works in any editor)
- `/o` command — save any conversation to your knowledge base in seconds
- Daily auto-ingest — every morning at 9am, new conversations are automatically processed
- Your language — notes generated in whatever language you choose

---

## macOS notice

The daily auto-ingest uses a macOS **launchd** agent to run every morning at 9am. On Linux or WSL, the setup script will print the equivalent `cron` command instead.

---

## Requirements

- macOS 12+ (or Linux/WSL with manual cron setup)
- Python 3.9+
- `pip install anthropic`
- Node.js (for MCP filesystem server: `npx @modelcontextprotocol/server-filesystem`)
- Anthropic API key ([get one here](https://console.anthropic.com))
- Claude Code installed

---

## Install

```bash
git clone https://github.com/yourusername/cc-knowledge ~/.claude/skills/cc-knowledge
cd ~/.claude/skills/cc-knowledge
./setup
```

Follow the 3 prompts:
1. Language for your notes (e.g. English, 中文, Español, 日本語)
2. Where to put your knowledge vault (default: `~/Documents/CC-Knowledge`)
3. Your Anthropic API key

Done. Restart Claude Code to pick up the new MCP server.

---

## Usage

### Manual save — /o command

At the end of any conversation worth remembering, type:

```
/o
```

Claude will:
1. Read `_system/index.md` to understand existing structure
2. Create a session recap in `session-recaps/`
3. Update or create concept library pages
4. Sync Q&As to `qa-handbook/`
5. Update the index and log

### Auto-save

Runs every morning at 9am automatically. No action required.

Check what ran:
```bash
tail -f ~/.cc-knowledge/ingest.log
```

### Manual ingest

```bash
# See what would happen without writing anything
python3 ~/.cc-knowledge/daily_ingest.py --dry-run

# Reprocess one specific conversation
python3 ~/.cc-knowledge/daily_ingest.py --force <uuid>

# Reprocess everything
python3 ~/.cc-knowledge/daily_ingest.py --all
```

---

## Vault structure

```
CC-Knowledge/
  _system/              — Index, log, schema (Claude reads these first)
  session-recaps/       — One file per conversation worth remembering
  concept-library/      — Tools, frameworks, APIs — one page per concept
  methodology/          — Reusable principles
  engineering-insights/ — Technical discoveries, gotchas
  mistake-log/          — Mistakes and how to avoid them
  projects/             — Project overviews
  open-source-library/  — Useful GitHub repos
  weekly-digest/        — Weekly summaries
  qa-handbook/          — Q&As organized by category
    claude-code-ops.md  — Claude Code features, commands, MCP
    git-github.md       — Git and GitHub workflows
    general.md          — General programming concepts
```

---

## Config file

`~/.cc-knowledge/config.json`:

```json
{
  "vault_path": "/Users/you/Documents/CC-Knowledge",
  "language": "English",
  "api_key": "sk-ant-..."
}
```

Edit this file to change settings. No need to re-run setup.

---

## Cost

Approximately $0.01–0.05 per conversation processed.
Roughly $0.30/month for daily use.

Models used:
- `claude-sonnet-4-6` — decision + recap generation
- `claude-haiku-4-5-20251001` — Q&A extraction + translation

---

## Uninstall

```bash
# Stop and remove launchd agent (macOS)
launchctl unload ~/Library/LaunchAgents/com.user.cc-knowledge.plist
rm ~/Library/LaunchAgents/com.user.cc-knowledge.plist

# Remove config and state
rm -rf ~/.cc-knowledge

# Remove MCP entry from ~/.claude.json (edit manually, remove "cc-knowledge" key)

# Optionally remove the vault
rm -rf ~/Documents/CC-Knowledge
```
