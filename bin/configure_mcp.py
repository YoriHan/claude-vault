#!/usr/bin/env python3
"""
configure_mcp.py — Merge cc-knowledge MCP server entry into ~/.claude.json

Called by setup. Does not clobber other MCP server entries.

Usage:
  python3 configure_mcp.py --vault /path/to/vault
"""

import argparse
import json
import sys
from pathlib import Path

CLAUDE_JSON = Path.home() / ".claude.json"


def load_claude_json() -> dict:
    if CLAUDE_JSON.exists():
        try:
            return json.loads(CLAUDE_JSON.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            print(f"Error: ~/.claude.json contains invalid JSON: {e}")
            print("Please fix the file manually, then re-run setup.")
            sys.exit(1)
    return {}


def save_claude_json(data: dict):
    CLAUDE_JSON.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8"
    )


def configure_mcp(vault_path: str):
    vault = Path(vault_path).expanduser().resolve()

    data = load_claude_json()

    # Ensure mcpServers key exists
    if "mcpServers" not in data:
        data["mcpServers"] = {}

    entry_key = "cc-knowledge"

    # Check if already configured with same path (idempotent)
    existing = data["mcpServers"].get(entry_key, {})
    existing_args = existing.get("args", [])
    if existing_args and str(vault) in existing_args:
        print(f"MCP entry '{entry_key}' already configured for {vault} — skipping")
        return

    # Merge in the cc-knowledge filesystem server entry
    data["mcpServers"][entry_key] = {
        "command": "npx",
        "args": [
            "-y",
            "@modelcontextprotocol/server-filesystem",
            str(vault)
        ],
        "type": "stdio"
    }

    save_claude_json(data)
    print(f"Configured MCP server '{entry_key}' pointing to: {vault}")
    print(f"Updated: {CLAUDE_JSON}")


def main():
    parser = argparse.ArgumentParser(
        description="Configure cc-knowledge MCP server in ~/.claude.json"
    )
    parser.add_argument("--vault", required=True,
                        help="Absolute path to the CC-Knowledge vault")
    args = parser.parse_args()

    configure_mcp(args.vault)


if __name__ == "__main__":
    main()
