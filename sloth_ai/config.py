"""
Configuration settings for SlothTidy AI.
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class SlothConfig:
    # Model configuration
    model_name: str = os.getenv("SLOTH_MODEL", "gemma2:2b")
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    temperature: float = 0.2
    
    # Workspace paths
    base_dir: Optional[Path] = None
    db_path: Path = field(init=False)
    inbox_dir: Path = field(init=False)
    archive_dir: Path = field(init=False)
    
    # Server configuration
    host: str = os.getenv("SLOTH_HOST", "127.0.0.1")
    port: int = int(os.getenv("SLOTH_PORT", "8765"))

    def __post_init__(self):
        if not self.base_dir:
            env_home = os.getenv("SLOTH_HOME")
            if env_home:
                self.base_dir = Path(env_home)
            else:
                # Default to project data directory or /tmp
                proj_data = Path(__file__).resolve().parent.parent / ".sloth_data"
                try:
                    proj_data.mkdir(parents=True, exist_ok=True)
                    self.base_dir = proj_data
                except Exception:
                    self.base_dir = Path("/tmp/sloth_ai")

        try:
            self.base_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            self.base_dir = Path("/tmp/sloth_ai")
            self.base_dir.mkdir(parents=True, exist_ok=True)

        self.db_path = self.base_dir / "sloth_memory.sqlite3"
        self.inbox_dir = self.base_dir / "inbox"
        self.archive_dir = self.base_dir / "organized"
        self.inbox_dir.mkdir(parents=True, exist_ok=True)
        self.archive_dir.mkdir(parents=True, exist_ok=True)

DEFAULT_CONFIG = SlothConfig()
