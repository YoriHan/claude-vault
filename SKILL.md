# /o — Session Knowledge Capture

Summarize the current conversation and file it into your CC-Knowledge vault.

**Language:** Check `_system/language.txt` in the vault. If it exists, write all content in that language. Otherwise default to English.

---

## Step 1: Read the index

Open `_system/index.md` via the filesystem MCP tool. Note:
- Existing session recap filenames (to avoid duplicates)
- Existing concept library pages (to update rather than duplicate)
- Current table structure

---

## Step 2: Create session recap

Create `session-recaps/YYYY-MM-DD Title.md` where:
- `YYYY-MM-DD` = the date this conversation took place (not today unless it happened today)
- `Title` = a short descriptive title (3–6 words, no slashes)

**File structure:**

```markdown
# YYYY-MM-DD Title

## Topic
One sentence describing the core of this conversation.

## What Was Done
- Specific action 1
- Specific action 2

## Methodology
What framework, approach, or mental model was applied?

## ✅ What Went Well
- Good judgment or decision worth repeating

## ⚠️ Could Be Better
- Where we went off track or what could be improved next time

## 💡 Principles
(2–4 reusable, cross-project principles extracted from this session)

**Principle Name:** Explanation

## 🔧 Engineering Insights
(Tools, APIs, technical discoveries, gotchas — omit section if none)

## 🙋 Q&As
(Scan the conversation for questions the user asked about operations, tools, or concepts)

### Q: [User's original question]
**Simple explanation:** 1–2 sentences, plain language, keep technical terms but explain them
**Docs pointer:** Suggest searching [relevant docs site] for [keyword] — do NOT fabricate specific URLs
```

If the file already exists (same date + title), skip creation and log a note.

---

## Step 3: Update concept library

For each tool, framework, API, or significant concept that appeared in this conversation:

1. Check `_system/index.md` — does a concept page already exist for this concept?
2. **If yes:** Open `concept-library/<Concept Name>.md` and append a new entry under the "Session Log" section:
   ```
   | YYYY-MM-DD | [brief note about how it was used] |
   ```
3. **If no:** Create `concept-library/<Concept Name>.md` with this structure:
   ```markdown
   # Concept Name

   **Category:** Tool / Framework / API / Pattern / Other
   **First seen:** YYYY-MM-DD

   ## What it is
   1–2 sentence explanation.

   ## How it was used
   Context from this conversation.

   ## Session Log
   | Date | Notes |
   |------|-------|
   | YYYY-MM-DD | Initial entry |
   ```

**Rule:** Update first. Create only when genuinely new.

---

## Step 4: Sync Q&As to qa-handbook

Take every Q&A from the 🙋 section of the recap and append to the correct file:

| Topic type | File |
|-----------|------|
| Claude Code features, slash commands, skills, MCP, hooks, settings | `qa-handbook/claude-code-ops.md` |
| git commands, GitHub workflows, PRs, branches, merging | `qa-handbook/git-github.md` |
| Everything else (general programming, frameworks, tools, concepts) | `qa-handbook/general.md` |

Format to append:
```markdown
## YYYY-MM-DD (session: Title)

### Q: [question]
**Simple explanation:** ...
**Docs pointer:** ...
```

Only append Q&As that are not already present in the file (check for the question text before appending).

---

## Step 5: Update index

In `_system/index.md`, add a new row to the Session Recaps table:

```
| session-recaps/YYYY-MM-DD Title.md | Title |
```

Insert the new row at the **top** of the table (most recent first), just below the table header line.

---

## Step 6: Write operation log

Append to `_system/log.md`:

```markdown
## [YYYY-MM-DD HH:MM] manual | /o | Title
**Created:** session-recaps/YYYY-MM-DD Title.md
**Updated:** [list concept library pages updated or created], [list qa-handbook files updated]
```

---

## Constraints

- **Vault path:** Read from the MCP filesystem server configuration — do not hardcode any path.
- **No fabricated links:** Never invent specific documentation URLs. Only suggest search terms.
- **Language:** Write all content in the language configured for this vault (read `_system/language.txt`; default English).
- **Concept library semantics:** Always check index before creating. Update existing pages, create new ones only when truly new.
- **Idempotency:** If a recap file already exists for this session, do not overwrite it. Append a note to the log instead.
