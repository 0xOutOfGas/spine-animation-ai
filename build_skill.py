#!/usr/bin/env python3
"""Build the concise Codex entrypoint; scripts remain independently executable."""
import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Check without writing")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    expected = (root / "SKILL.template.md").read_text(encoding="utf-8")
    destination = root / "SKILL.md"
    if args.check:
        if not destination.exists() or destination.read_text(encoding="utf-8") != expected:
            parser.exit(1, "SKILL.md is stale; run python build_skill.py\n")
        print("Codex entrypoint is current")
    else:
        destination.write_text(expected, encoding="utf-8")
        print(f"Built SKILL.md ({len(expected.splitlines())} lines; no embedded scripts)")


if __name__ == "__main__":
    main()
