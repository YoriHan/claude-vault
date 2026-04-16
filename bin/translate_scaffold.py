#!/usr/bin/env python3
"""
translate_scaffold.py — Translate scaffold template files into the user's chosen language.

Called by setup when language != English.

Usage:
  python3 translate_scaffold.py --language 中文 --vault-dir /path/to/vault --api-key sk-ant-...
"""

import argparse
import json
import os
import sys
from pathlib import Path

import anthropic


def translate_text(client: anthropic.Anthropic, text: str, language: str) -> str:
    """Translate text to target language using claude-haiku for speed and cost."""
    resp = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=4096,
        system=(
            f"You are a technical translator. Translate the following Markdown text to {language}. "
            "Rules:\n"
            "- Preserve all Markdown formatting (headers, tables, code blocks, bold, etc.)\n"
            "- Keep technical terms, tool names, and code snippets in English\n"
            "- Keep emoji as-is\n"
            "- Keep file paths and URLs as-is\n"
            "- Translate only human-readable prose and headers\n"
            "Output only the translated Markdown, no preamble."
        ),
        messages=[{"role": "user", "content": text}]
    )
    return resp.content[0].text.strip()


def translate_file(client: anthropic.Anthropic, file_path: Path, language: str):
    """Read, translate, and overwrite a single file."""
    original = file_path.read_text(encoding="utf-8")
    print(f"  Translating: {file_path.name} ...", end=" ", flush=True)
    try:
        translated = translate_text(client, original, language)
        file_path.write_text(translated, encoding="utf-8")
        print("done")
    except anthropic.APIError as e:
        print(f"ERROR: {e}")
        print(f"  Keeping original English content for {file_path.name}")


def write_language_file(vault_dir: Path, language: str):
    """Write _system/language.txt so /o command knows the vault language."""
    lang_file = vault_dir / "_system" / "language.txt"
    lang_file.write_text(language + "\n", encoding="utf-8")
    print(f"  Written: _system/language.txt ({language})")


def main():
    parser = argparse.ArgumentParser(
        description="Translate CC-Knowledge scaffold files into the user's language"
    )
    parser.add_argument("--language", required=True,
                        help="Target language (e.g. 中文, Español, 日本語)")
    parser.add_argument("--vault-dir", required=True,
                        help="Path to the installed vault directory")
    parser.add_argument("--api-key", default="",
                        help="Anthropic API key (falls back to ANTHROPIC_API_KEY env var)")
    args = parser.parse_args()

    api_key = args.api_key or os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("Error: Anthropic API key required (--api-key or ANTHROPIC_API_KEY)")
        sys.exit(1)

    vault_dir = Path(args.vault_dir).expanduser().resolve()
    if not vault_dir.exists():
        print(f"Error: vault directory not found: {vault_dir}")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    print(f"Translating scaffold to {args.language}...")

    # Files to translate (key content files that users will read regularly)
    files_to_translate = [
        vault_dir / "_system" / "index.md",
        vault_dir / "_system" / "SCHEMA.md",
        vault_dir / "_system" / "log.md",
        vault_dir / "mistake-log" / "mistake-log.md",
        vault_dir / "qa-handbook" / "claude-code-ops.md",
        vault_dir / "qa-handbook" / "git-github.md",
        vault_dir / "qa-handbook" / "general.md",
    ]

    for file_path in files_to_translate:
        if file_path.exists():
            translate_file(client, file_path, args.language)
        else:
            print(f"  SKIP (not found): {file_path.name}")

    # Write language marker file
    write_language_file(vault_dir, args.language)

    print(f"\nTranslation complete. Vault language set to: {args.language}")


if __name__ == "__main__":
    main()
