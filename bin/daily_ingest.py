#!/usr/bin/env python3
"""
daily_ingest.py — Automatically document Claude Code conversations into your CC-Knowledge vault.

Reads config from ~/.cc-knowledge/config.json

Usage:
  python3 daily_ingest.py           # normal run
  python3 daily_ingest.py --dry-run # print actions, write nothing
  python3 daily_ingest.py --force <uuid>  # reprocess one specific file
  python3 daily_ingest.py --all     # reprocess all files
"""

import json
import os
import sys
import re
import argparse
from pathlib import Path
from datetime import datetime, timezone

import anthropic

# ── Config ──────────────────────────────────────────────────────────────────

CONFIG_FILE = Path.home() / ".cc-knowledge" / "config.json"
STATE_FILE  = Path.home() / ".cc-knowledge" / "ingest_state.json"
LOG_FILE    = Path.home() / ".cc-knowledge" / "ingest.log"
JSONL_ROOT  = Path.home() / ".claude" / "projects"

MIN_USER_MESSAGES = 4    # minimum user messages to consider documenting
COOLDOWN_MINUTES  = 60   # skip files modified less than this many minutes ago

QA_TOPIC_FILES = {
    "Claude Code Operations": "qa-handbook/claude-code-ops.md",
    "Git & GitHub":           "qa-handbook/git-github.md",
    "General":                "qa-handbook/general.md",
}


def load_config() -> dict:
    if not CONFIG_FILE.exists():
        print(f"Error: config file not found at {CONFIG_FILE}")
        print("Run ./setup first to configure cc-knowledge.")
        sys.exit(1)
    try:
        cfg = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"Error: invalid JSON in {CONFIG_FILE}: {e}")
        sys.exit(1)
    required = ("vault_path", "api_key")
    for key in required:
        if key not in cfg:
            print(f"Error: missing '{key}' in {CONFIG_FILE}")
            sys.exit(1)
    return cfg


# ── Globals (set after config load) ─────────────────────────────────────────

config       = load_config()
NOTEBOOK_DIR = Path(config["vault_path"])
LANGUAGE     = config.get("language", "English")

# API key: config file takes priority, fall back to env var
api_key = config.get("api_key") or os.environ.get("ANTHROPIC_API_KEY", "")
if not api_key:
    print("Error: no Anthropic API key found in config or ANTHROPIC_API_KEY env var.")
    sys.exit(1)
os.environ["ANTHROPIC_API_KEY"] = api_key

client = anthropic.Anthropic(api_key=api_key)


# ── Logging ──────────────────────────────────────────────────────────────────

def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


# ── State management ─────────────────────────────────────────────────────────

def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {"processed": {}}
    return {"processed": {}}


def save_state(state: dict):
    STATE_FILE.write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


# ── JSONL parsing ─────────────────────────────────────────────────────────────

def extract_conversation(jsonl_path: Path) -> list[dict]:
    messages = []
    with open(jsonl_path, encoding="utf-8") as fp:
        for line in fp:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if obj.get("type") not in ("user", "assistant"):
                continue
            msg = obj.get("message", {})
            role = msg.get("role", "")
            content = msg.get("content", "")
            ts = obj.get("timestamp", "")
            text = ""
            if isinstance(content, list):
                for c in content:
                    if isinstance(c, dict) and c.get("type") == "text":
                        text += c.get("text", "")
            else:
                text = str(content or "")
            text = text.strip()
            if text:
                messages.append({"role": role, "ts": ts[:19], "text": text})
    return messages


def format_conversation(messages: list[dict], max_chars: int = 25000) -> str:
    lines = []
    total = 0
    for m in messages:
        prefix = "User" if m["role"] == "user" else "Claude"
        line = f"[{prefix} {m['ts']}]\n{m['text']}\n"
        total += len(line)
        if total > max_chars:
            lines.append("\n[... conversation truncated ...]")
            break
        lines.append(line)
    return "\n".join(lines)


# ── Phase 1: Decision API ─────────────────────────────────────────────────────

DECISION_SYSTEM = """You are the maintenance assistant for CC-Knowledge, a Karpathy Wiki-style personal knowledge base.
Analyze a Claude Code conversation and decide whether it is worth documenting.

Output strict JSON only (no other text):
{{
  "should_document": true/false,
  "skip_reason": "if not documenting, brief reason; otherwise empty string",
  "date": "YYYY-MM-DD (date the conversation happened, not today)",
  "title": "topic title (10 words or fewer)",
  "has_qa": true/false,
  "qa_topics": ["Claude Code Operations", "Git & GitHub", "General"],
  "new_concepts": ["list of new tools or concepts mentioned, e.g. Whisper, Notion API"],
  "has_mistake": true/false
}}

Worth documenting:
- Substantive technical discussion, tool usage, or problem solving → true
- New concepts or tools appear → true
- Just greetings, very short tests, or no real content → false

Respond in English regardless of the conversation language."""


def call_decision_api(conv_text: str) -> dict | None:
    try:
        resp = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=512,
            system=DECISION_SYSTEM,
            messages=[{"role": "user", "content": f"Analyze this conversation:\n\n{conv_text[:8000]}"}]
        )
        raw = resp.content[0].text.strip()
        raw = re.sub(r"^```json\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        return json.loads(raw)
    except (json.JSONDecodeError, anthropic.APIError) as e:
        log(f"  WARNING: decision API failed: {e}")
        return None


# ── Phase 2a: Recap generation API ──────────────────────────────────────────

RECAP_SYSTEM = f"""You are the content generation assistant for CC-Knowledge.
Generate a session recap Markdown file based on the conversation provided.

IMPORTANT: Write all content in {LANGUAGE}.

Format:
# YYYY-MM-DD Title

## Topic
One sentence describing the core of this conversation.

## What Was Done
- Specific item 1
- Specific item 2

## Methodology
What framework or approach was used?

## ✅ What Went Well
- Good judgment or decision worth repeating

## ⚠️ Could Be Better
- Where things went off track or could improve

## 💡 Principles
(2-4 reusable, cross-project principles)

**Principle Name:** Explanation

## 🔧 Engineering Insights
(Tools, APIs, technical discoveries, gotchas — omit section if none)

## 🙋 Q&As
(Questions the user asked about operations, concepts, or tools)

### Q: [User's original question]
**Simple explanation:** 1-2 sentences, plain language, keep technical terms but explain them
**Docs pointer:** Suggest searching [relevant docs site] for [keyword] — do NOT fabricate specific URLs

Output only the Markdown content. No JSON, no preamble."""


def call_recap_api(conv_text: str, date: str, title: str) -> str:
    try:
        resp = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=3000,
            system=RECAP_SYSTEM,
            messages=[{"role": "user", "content": f"Generate a session recap for this conversation (date: {date}, topic: {title}):\n\n{conv_text}"}]
        )
        return resp.content[0].text.strip()
    except anthropic.APIError as e:
        log(f"  WARNING: recap API failed: {e}")
        return ""


# ── Phase 2b: Q&A extraction API ─────────────────────────────────────────────

QA_SYSTEM = f"""You are a Q&A handbook organizer. Extract user questions about operations, tools, or concepts from the conversation and format them as Q&A entries.

IMPORTANT: Write all content in {LANGUAGE}.

Output only the following Markdown format, no preamble:

### Q: [User's original question]
**Simple explanation:** 1-2 sentences, plain language, keep technical terms but explain them
**Docs pointer:** Suggest searching [relevant docs site] for [keyword] — do NOT fabricate specific URLs

Separate each Q&A with a blank line. If there are no clear operational or learning questions in the conversation, output only the word "none"."""


def call_qa_api(conv_text: str, category: str) -> str:
    try:
        resp = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1000,
            system=QA_SYSTEM,
            messages=[{"role": "user", "content": f"Category: {category}\n\nConversation:\n\n{conv_text[:6000]}"}]
        )
        return resp.content[0].text.strip()
    except anthropic.APIError as e:
        log(f"  WARNING: Q&A API failed: {e}")
        return ""


# ── File I/O ──────────────────────────────────────────────────────────────────

def write_file(rel_path: str, content: str, dry_run: bool):
    abs_path = NOTEBOOK_DIR / rel_path
    if dry_run:
        log(f"  [DRY-RUN] would create: {rel_path} ({len(content)} chars)")
        return
    abs_path.parent.mkdir(parents=True, exist_ok=True)
    if abs_path.exists():
        log(f"  SKIP (already exists): {rel_path}")
    else:
        abs_path.write_text(content, encoding="utf-8")
        log(f"  Created: {rel_path}")


def append_to_file(rel_path: str, content: str, dry_run: bool):
    abs_path = NOTEBOOK_DIR / rel_path
    if dry_run:
        log(f"  [DRY-RUN] would append to: {rel_path}")
        return
    if abs_path.exists():
        existing = abs_path.read_text(encoding="utf-8")
        abs_path.write_text(
            existing.rstrip() + "\n\n" + content + "\n",
            encoding="utf-8"
        )
        log(f"  Appended to: {rel_path}")
    else:
        log(f"  WARNING: append target not found: {rel_path}")


def update_index(date: str, title: str, recap_path: str, dry_run: bool):
    index_file = NOTEBOOK_DIR / "_system" / "index.md"
    recap_name = Path(recap_path).name
    new_row = f"| {recap_name} | {title} |"
    marker = "<!-- new rows inserted above this line by /o and daily_ingest -->"

    if dry_run:
        log(f"  [DRY-RUN] would insert into index.md: {new_row}")
        return

    if not index_file.exists():
        log(f"  WARNING: index.md not found at {index_file}")
        return

    existing = index_file.read_text(encoding="utf-8")
    if recap_name in existing:
        log("  index.md already contains this recap — skipping")
        return

    if marker in existing:
        updated = existing.replace(marker, f"{new_row}\n{marker}", 1)
        index_file.write_text(updated, encoding="utf-8")
        log("  Updated _system/index.md")
    else:
        # Fallback: append to end of Session Recaps section
        log("  WARNING: index.md marker not found — appending row at end")
        index_file.write_text(existing.rstrip() + f"\n{new_row}\n", encoding="utf-8")


def update_log(date: str, title: str, files_created: list[str], source: str, dry_run: bool):
    log_file = NOTEBOOK_DIR / "_system" / "log.md"
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    files_str = ", ".join(files_created) if files_created else "(none)"
    entry = (
        f"\n## [{now_str}] auto-ingest | daily_ingest | {title}\n"
        f"**Created:** {files_str}\n"
        f"**Source:** {source}\n"
    )
    if dry_run:
        log(f"  [DRY-RUN] would append to log.md: {title}")
        return
    if log_file.exists():
        existing = log_file.read_text(encoding="utf-8")
        log_file.write_text(existing.rstrip() + "\n" + entry, encoding="utf-8")
        log("  Updated _system/log.md")
    else:
        log(f"  WARNING: log.md not found at {log_file}")


# ── Main processing ───────────────────────────────────────────────────────────

def process_file(jsonl_path: Path, state: dict, dry_run: bool = False) -> bool:
    # State key: relative path from JSONL_ROOT to handle multiple projects
    try:
        rel_key = str(jsonl_path.relative_to(JSONL_ROOT))
    except ValueError:
        rel_key = str(jsonl_path)

    now = datetime.now(tz=timezone.utc)

    # Cooldown check
    mtime = datetime.fromtimestamp(jsonl_path.stat().st_mtime, tz=timezone.utc)
    age_min = (now - mtime).total_seconds() / 60
    if age_min < COOLDOWN_MINUTES:
        log(f"  SKIP (modified {age_min:.0f}m ago — conversation may still be active)")
        return False

    # Extract and check conversation length
    messages = extract_conversation(jsonl_path)
    user_msgs = [m for m in messages if m["role"] == "user"]
    if len(user_msgs) < MIN_USER_MESSAGES:
        log(f"  SKIP (only {len(user_msgs)} user messages, need {MIN_USER_MESSAGES})")
        state["processed"][rel_key] = {
            "processed_at": now.isoformat(),
            "skipped": True,
            "reason": "too_short"
        }
        return False

    conv_text = format_conversation(messages)
    log(f"  Conversation: {len(messages)} messages, {len(conv_text)} chars")

    # Phase 1: Decision
    log("  Phase 1: deciding whether to document...")
    decision = call_decision_api(conv_text)
    if decision is None:
        return False

    if not decision.get("should_document", False):
        reason = decision.get("skip_reason", "not specified")
        log(f"  SKIP: {reason}")
        state["processed"][rel_key] = {
            "processed_at": now.isoformat(),
            "skipped": True,
            "reason": reason
        }
        return False

    date  = decision.get("date", now.strftime("%Y-%m-%d"))
    title = decision.get("title", "Untitled Session")
    log(f"  Date: {date}, Title: {title}")

    files_created = []

    # Phase 2a: Generate recap
    log("  Phase 2a: generating session recap...")
    recap_content = call_recap_api(conv_text, date, title)
    if recap_content:
        recap_path = f"session-recaps/{date} {title}.md"
        write_file(recap_path, recap_content, dry_run)
        files_created.append(recap_path)

    # Phase 2b: Extract Q&As for each relevant topic
    if decision.get("has_qa"):
        qa_topics = decision.get("qa_topics", [])
        for topic in qa_topics:
            qa_file = QA_TOPIC_FILES.get(topic)
            if not qa_file:
                continue
            log(f"  Phase 2b: extracting Q&As for '{topic}'...")
            qa_content = call_qa_api(conv_text, topic)
            if qa_content and qa_content.lower() not in ("none", "无"):
                qa_section = f"## {date} (auto-ingest)\n\n{qa_content}"
                append_to_file(qa_file, qa_section, dry_run)

    # Post-processing
    if files_created:
        update_index(date, title, files_created[0], dry_run)
        update_log(date, title, files_created, rel_key, dry_run)

    state["processed"][rel_key] = {
        "processed_at": now.isoformat(),
        "date": date,
        "title": title,
        "files": files_created,
    }
    log(f"  Done: {title}")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Ingest Claude Code conversations into CC-Knowledge vault."
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Print what would happen without writing files")
    parser.add_argument("--force", metavar="UUID",
                        help="Reprocess one specific JSONL file (by uuid or filename)")
    parser.add_argument("--all", action="store_true",
                        help="Reprocess all files regardless of state")
    args = parser.parse_args()

    log("=" * 60)
    log("daily_ingest started" + (" [dry-run]" if args.dry_run else ""))
    log(f"Vault: {NOTEBOOK_DIR}")
    log(f"Language: {LANGUAGE}")

    if not JSONL_ROOT.exists():
        log(f"ERROR: JSONL root not found: {JSONL_ROOT}")
        sys.exit(1)

    state = load_state()
    jsonl_files = sorted(JSONL_ROOT.rglob("*.jsonl"), key=lambda f: f.stat().st_mtime)
    log(f"Found {len(jsonl_files)} JSONL files")

    done = skip = 0
    for jsonl_path in jsonl_files:
        try:
            rel_key = str(jsonl_path.relative_to(JSONL_ROOT))
        except ValueError:
            rel_key = str(jsonl_path)

        if args.force:
            force_id = args.force if args.force.endswith(".jsonl") else args.force + ".jsonl"
            # Match by filename (last component) or full relative path
            if jsonl_path.name != force_id and not rel_key.endswith(force_id):
                continue
            state["processed"].pop(rel_key, None)
        elif args.all:
            state["processed"].pop(rel_key, None)
        elif rel_key in state["processed"]:
            skip += 1
            continue

        log(f"\nProcessing: {rel_key}")
        if process_file(jsonl_path, state, dry_run=args.dry_run):
            done += 1

    if not args.dry_run:
        save_state(state)

    log(f"\nDone: processed {done}, skipped {skip} already-processed files")
    log("=" * 60)


if __name__ == "__main__":
    main()
