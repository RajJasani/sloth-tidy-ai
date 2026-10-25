"""
Command Line Interface for SlothTidy AI.
"""

import sys
import argparse
from pathlib import Path
from sloth_ai.config import DEFAULT_CONFIG
from sloth_ai.core.engine import LocalAIEngine
from sloth_ai.modules.storage import SlothStorage
from sloth_ai.modules.tidier import SlothTidier
from sloth_ai.modules.digest import SlothDigest
from sloth_ai.server.app import run_server

def main():
    parser = argparse.ArgumentParser(
        description="SlothTidy AI - Open-Source Local Ambient Workspace Optimizer"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Command: status
    subparsers.add_parser("status", help="Show system status and local AI model health")

    # Command: tidy
    tidy_parser = subparsers.add_parser("tidy", help="Organize files in inbox or target folder")
    tidy_parser.add_argument("--folder", type=str, default=None, help="Target directory to tidy")
    tidy_parser.add_argument("--dry-run", action="store_true", help="Audit without moving files")

    # Command: digest
    digest_parser = subparsers.add_parser("digest", help="Generate executive morning briefing from notes")
    digest_parser.add_argument("--file", type=str, default=None, help="Path to markdown/text notes file")
    digest_parser.add_argument("--folder", type=str, default=None, help="Folder containing daily notes")

    # Command: serve
    serve_parser = subparsers.add_parser("serve", help="Launch the local Web Dashboard and REST API")
    serve_parser.add_argument("--port", type=int, default=8765, help="Port to bind server")
    serve_parser.add_argument("--host", type=str, default="127.0.0.1", help="Host address")

    args = parser.parse_args()

    if not args.command or args.command == "status":
        engine = LocalAIEngine()
        storage = SlothStorage()
        health = engine.check_health()
        stats = storage.stats()
        print("=" * 55)
        print("🦥  SlothTidy AI - Ambient Workspace Optimizer")
        print("=" * 55)
        print(f"• Engine Type:        {health['engine']}")
        print(f"• Configured Model:   {health['model']}")
        print(f"• Ollama Connected:   {'Yes' if health['ollama_connected'] else 'No (Using Local Fallback)'}")
        print(f"• Privacy Guarantee:  {health['privacy_mode']}")
        print(f"• Files Organized:    {stats['total_organized_files']}")
        print(f"• Morning Briefings:  {stats['total_digests_generated']}")
        print("=" * 55)
        return

    if args.command == "tidy":
        tidier = SlothTidier()
        folder = Path(args.folder) if args.folder else None
        print(f"🔍 Scanning files in: {folder or DEFAULT_CONFIG.inbox_dir}...")
        results = tidier.scan_and_tidy(source_dir=folder, dry_run=args.dry_run)
        if not results:
            print("✨ Everything is already clean and organized!")
            return
        
        mode_str = "[DRY RUN] " if args.dry_run else ""
        print(f"\n{mode_str}Successfully processed {len(results)} files:")
        for res in results:
            fname = Path(res['source']).name
            print(f"  • {fname}  -->  [{res['category']}]")
            print(f"    Summary: {res['summary']}\n")

    elif args.command == "digest":
        digest_gen = SlothDigest()
        if args.folder:
            res = digest_gen.generate_digest_from_folder(Path(args.folder))
        elif args.file:
            path = Path(args.file)
            content = path.read_text(encoding="utf-8") if path.exists() else ""
            res = digest_gen.generate_digest_from_text(content, f"Digest - {path.name}")
        else:
            sample_notes = (
                "- Implement local test cases\n"
                "- Review Hacktoberfest Week 3 guidelines\n"
                "- Prepare morning slide presentation"
            )
            print("ℹ️  No file specified. Using sample notes demonstration:\n")
            res = digest_gen.generate_digest_from_text(sample_notes)

        print("=" * 55)
        print(f"🌅  {res.get('title', 'Morning Digest')}")
        print("=" * 55)
        print(f"Overview:\n{res.get('summary', '')}\n")
        print("Action Items:")
        for it in res.get("action_items", []):
            print(f"  [ ] {it}")
        print(f"\nSloth Wisdom: \"{res.get('sloth_wisdom', '')}\"")
        print("=" * 55)

    elif args.command == "serve":
        run_server(host=args.host, port=args.port)

if __name__ == "__main__":
    main()
