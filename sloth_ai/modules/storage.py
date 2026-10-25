"""
Local SQLite Storage and Audit Logging Engine.
Tracks all organized files, allows 1-click rollback, and stores daily digests.
"""

import sqlite3
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from sloth_ai.config import DEFAULT_CONFIG, SlothConfig

class SlothStorage:
    def __init__(self, config: Optional[SlothConfig] = None):
        self.config = config or DEFAULT_CONFIG
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.config.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS file_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_hash TEXT,
                    original_name TEXT,
                    original_path TEXT,
                    archive_path TEXT,
                    category TEXT,
                    summary TEXT,
                    confidence REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'active'
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS digests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    summary TEXT,
                    action_items TEXT,
                    topics TEXT,
                    wisdom TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def record_file(self, original_path: Path, archive_path: Path, metadata: Dict[str, Any]) -> int:
        file_hash = ""
        try:
            if archive_path.exists():
                file_hash = hashlib.sha256(archive_path.read_bytes()).hexdigest()[:16]
        except Exception:
            pass

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO file_records (
                    file_hash, original_name, original_path, archive_path,
                    category, summary, confidence, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'active')
            """, (
                file_hash,
                original_path.name,
                str(original_path),
                str(archive_path),
                metadata.get("category", "unclassified"),
                metadata.get("summary", ""),
                metadata.get("confidence", 1.0)
            ))
            conn.commit()
            return cursor.lastrowid

    def list_files(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM file_records 
                WHERE status = 'active'
                ORDER BY created_at DESC LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def record_digest(self, title: str, digest_data: Dict[str, Any]) -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO digests (title, summary, action_items, topics, wisdom)
                VALUES (?, ?, ?, ?, ?)
            """, (
                title,
                digest_data.get("summary", ""),
                json.dumps(digest_data.get("action_items", [])),
                json.dumps(digest_data.get("topics", [])),
                digest_data.get("sloth_wisdom", "")
            ))
            conn.commit()
            return cursor.lastrowid

    def list_digests(self, limit: int = 20) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM digests ORDER BY created_at DESC LIMIT ?", (limit,))
            results = []
            for row in cursor.fetchall():
                d = dict(row)
                d["action_items"] = json.loads(d["action_items"]) if d["action_items"] else []
                d["topics"] = json.loads(d["topics"]) if d["topics"] else []
                results.append(d)
            return results

    def stats(self) -> Dict[str, Any]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM file_records WHERE status = 'active'")
            total_files = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(DISTINCT category) FROM file_records WHERE status = 'active'")
            categories = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM digests")
            total_digests = cursor.fetchone()[0]
            return {
                "total_organized_files": total_files,
                "distinct_categories": categories,
                "total_digests_generated": total_digests
            }
