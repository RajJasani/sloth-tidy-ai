"""
Ambient Overnight & Daily Digest Engine.
Processes raw notes, git commits, and unorganized task logs into a serene morning briefing.
"""

from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
from sloth_ai.config import DEFAULT_CONFIG, SlothConfig
from sloth_ai.core.engine import LocalAIEngine
from sloth_ai.modules.storage import SlothStorage

class SlothDigest:
    def __init__(self, engine: Optional[LocalAIEngine] = None, storage: Optional[SlothStorage] = None, config: Optional[SlothConfig] = None):
        self.config = config or DEFAULT_CONFIG
        self.engine = engine or LocalAIEngine(self.config)
        self.storage = storage or SlothStorage(self.config)

    def generate_digest_from_text(self, text: str, title: Optional[str] = None) -> Dict[str, Any]:
        """Generate a structured digest from raw text content."""
        if not text.strip():
            return {
                "summary": "No logs or notes provided to summarize.",
                "action_items": [],
                "topics": [],
                "sloth_wisdom": "Rest is productive. Enjoy your peace."
            }

        digest_data = self.engine.extract_digest(text)
        final_title = title or f"Morning Digest - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        digest_id = self.storage.record_digest(final_title, digest_data)
        digest_data["id"] = digest_id
        digest_data["title"] = final_title
        return digest_data

    def generate_digest_from_folder(self, notes_dir: Path) -> Dict[str, Any]:
        """Scan a folder containing daily notes, markdown docs, and logs."""
        folder = Path(notes_dir)
        if not folder.exists():
            return self.generate_digest_from_text("", "Empty Notes Directory")

        combined_text = []
        for file_path in sorted(folder.iterdir()):
            if file_path.is_file() and file_path.suffix.lower() in {".txt", ".md", ".log"}:
                try:
                    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                        combined_text.append(f"--- File: {file_path.name} ---\n{f.read(2048)}\n")
                except Exception:
                    pass

        raw_content = "\n".join(combined_text)
        return self.generate_digest_from_text(raw_content, f"Overnight Digest - {datetime.now().strftime('%B %d, %Y')}")
