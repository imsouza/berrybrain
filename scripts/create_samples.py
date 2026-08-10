from __future__ import annotations

import argparse
from pathlib import Path

from berrybrain_api.config import get_settings
from berrybrain_api.vault import create_note


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a BerryBrain sample note")
    parser.add_argument("source", type=Path, help="Markdown file to import")
    parser.add_argument("--title", required=True, help="Title for the new note")
    parser.add_argument("--folder", required=True, help="Target vault folder")
    args = parser.parse_args()
    content = args.source.expanduser().resolve().read_text(encoding="utf-8")
    note = create_note(
        get_settings().vault_path,
        args.title,
        args.folder,
        content,
    )
    print(f"Created {note['path']}")


if __name__ == "__main__":
    main()
