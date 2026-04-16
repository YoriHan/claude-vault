# CC-Knowledge · Working Manual

## Core Principle (Karpathy Wiki)

Same concept = one page. Update existing pages, create new only when truly new.

---

## /o Command

Run `/o` at the end of any valuable Claude Code conversation to save it.

Claude will:
1. Read `_system/index.md` to understand what already exists
2. Create a session recap in `session-recaps/`
3. Update or create concept library pages
4. Sync Q&As to the appropriate `qa-handbook/` file
5. Update `_system/index.md` and `_system/log.md`

---

## Auto-Ingest

`daily_ingest.py` runs every morning at 9am and processes new conversations automatically.

It scans `~/.claude/projects/` for new JSONL files, decides if they're worth documenting, generates session recaps, extracts Q&As, and updates the index and log.

Manual flags:
- `--dry-run` — print what would happen, write nothing
- `--force <uuid>` — reprocess one specific conversation file
- `--all` — reprocess all conversation files

---

## Directory Structure

| Folder | Purpose |
|--------|---------|
| `_system/` | Index, log, schema — system files read by Claude |
| `session-recaps/` | One file per conversation worth remembering |
| `concept-library/` | Tools, frameworks, APIs — one page per concept |
| `methodology/` | Reusable principles across projects |
| `engineering-insights/` | Technical discoveries, gotchas, patterns |
| `mistake-log/` | Mistakes and how to avoid them |
| `projects/` | Per-project overviews |
| `open-source-library/` | GitHub projects you've found useful |
| `weekly-digest/` | Weekly summaries |
| `qa-handbook/` | Q&As from conversations, organized by category |

---

## File Naming

- Session recaps: `YYYY-MM-DD Short Title.md`
- Concept library: `Concept Name.md` (title case, spaces allowed)
- No special characters in filenames except spaces and hyphens

---

## Adding Entries Manually

You can add entries to any file directly. The system will not overwrite existing files — it only appends or creates new ones.

To manually add to the mistake log, follow the format in `mistake-log/mistake-log.md`.
To manually add a concept, create a file in `concept-library/` and add a row to `_system/index.md`.
