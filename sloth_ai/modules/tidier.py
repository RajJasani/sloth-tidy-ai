"""
Autonomous File & Inbox Tidier.
Scans messy directories, understands file context with open-weight AI,
and organizes them into clean, structured categories.
"""

import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
from sloth_ai.config import DEFAULT_CONFIG, SlothConfig
from sloth_ai.core.engine import LocalAIEngine
from sloth_ai.modules.storage import SlothStorage

TEXT_EXTENSIONS = {".txt", ".md", ".py", ".js", ".ts", ".json", ".csv", ".log", ".html", ".css", ".sh", ".yml", ".yaml"}

class SlothTidier:
    def __init__(self, engine: Optional[LocalAIEngine] = None, storage: Optional[SlothStorage] = None, config: Optional[SlothConfig] = None):
        self.config = config or DEFAULT_CONFIG
        self.engine = engine or LocalAIEngine(self.config)
        self.storage = storage or SlothStorage(self.config)

    def _read_file_snippet(self, file_path: Path, max_bytes: int = 4096) -> str:
        """Safely extract readable snippet from text or provide binary metadata."""
        if file_path.suffix.lower() in TEXT_EXTENSIONS:
            try:
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    return f.read(max_bytes)
            except Exception:
                return f"[File {file_path.name} of size {file_path.stat().st_size} bytes]"
        return f"[Binary file {file_path.name} of size {file_path.stat().st_size} bytes with extension {file_path.suffix}]"

    def scan_and_tidy(self, source_dir: Optional[Path] = None, dry_run: bool = False) -> List[Dict[str, Any]]:
        """Scan source directory and tidy all eligible files."""
        folder = Path(source_dir) if source_dir else self.config.inbox_dir
        if not folder.exists():
            return []

        results = []
        for file_path in folder.iterdir():
            if file_path.is_file() and not file_path.name.startswith("."):
                snippet = self._read_file_snippet(file_path)
                classification = self.engine.classify_document(file_path.name, snippet)
                
                category = classification.get("category", "unclassified")
                target_category_dir = self.config.archive_dir / category
                target_path = target_category_dir / file_path.name

                item_record = {
                    "source": str(file_path),
                    "target": str(target_path),
                    "category": category,
                    "summary": classification.get("summary", ""),
                    "confidence": classification.get("confidence", 1.0),
                    "dry_run": dry_run
                }

                if not dry_run:
                    target_category_dir.mkdir(parents=True, exist_ok=True)
                    # Handle duplicate filenames
                    counter = 1
                    final_target = target_path
                    while final_target.exists():
                        stem = file_path.stem
                        ext = file_path.suffix
                        final_target = target_category_dir / f"{stem}_{counter}{ext}"
                        counter += 1

                    shutil.move(str(file_path), str(final_target))
                    item_record["target"] = str(final_target)
                    self.storage.record_file(file_path, final_target, classification)

                results.append(item_record)

        return results
