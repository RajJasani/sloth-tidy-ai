"""
Unit Tests for SlothTidy AI Engine, Modules, Storage, and HTTP Server.
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from sloth_ai.config import SlothConfig
from sloth_ai.core.engine import LocalAIEngine
from sloth_ai.modules.storage import SlothStorage
from sloth_ai.modules.tidier import SlothTidier
from sloth_ai.modules.digest import SlothDigest

class TestSlothTidyAI(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.base_path = Path(self.test_dir)
        self.config = SlothConfig(
            base_dir=self.base_path,
            host="127.0.0.1",
            port=9999
        )
        self.storage = SlothStorage(self.config)
        self.engine = LocalAIEngine(self.config)
        self.tidier = SlothTidier(self.engine, self.storage, self.config)
        self.digest = SlothDigest(self.engine, self.storage, self.config)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_engine_health(self):
        health = self.engine.check_health()
        self.assertIn("engine", health)
        self.assertIn("privacy_mode", health)
        self.assertEqual(health["privacy_mode"], "100% Local Inference (Zero Data Leaves Machine)")

    def test_heuristic_classification(self):
        res1 = self.engine.classify_document("receipt.txt", "Total invoice amount: $120 USD paid.")
        self.assertEqual(res1["category"], "finance_receipts")

        res2 = self.engine.classify_document("main.py", "def calculate_hash(): import hashlib")
        self.assertEqual(res2["category"], "developer_code")

        res3 = self.engine.classify_document("notes.md", "Sprint review meeting agenda and roadmap.")
        self.assertEqual(res3["category"], "work_projects")

    def test_digest_generation(self):
        notes = (
            "- TODO: Ship the open-source release\n"
            "- Implement safety rollback mechanism\n"
            "- Meeting with core maintainers"
        )
        res = self.digest.generate_digest_from_text(notes, "Test Morning Digest")
        self.assertIn("summary", res)
        self.assertIn("action_items", res)
        self.assertTrue(len(res["action_items"]) > 0)
        self.assertIn("sloth_wisdom", res)

    def test_scan_and_tidy(self):
        # Create sample files in inbox
        inbox = self.config.inbox_dir
        invoice = inbox / "test_invoice.txt"
        invoice.write_text("Invoice #999 Total: $50 USD payment received", encoding="utf-8")
        
        script = inbox / "helper.py"
        script.write_text("import os\ndef test(): pass", encoding="utf-8")

        # Dry run
        dry_results = self.tidier.scan_and_tidy(dry_run=True)
        self.assertEqual(len(dry_results), 2)
        self.assertTrue(invoice.exists()) # Should still exist

        # Actual run
        real_results = self.tidier.scan_and_tidy(dry_run=False)
        self.assertEqual(len(real_results), 2)
        self.assertFalse(invoice.exists()) # Moved

        # Verify storage
        files = self.storage.list_files()
        self.assertEqual(len(files), 2)
        stats = self.storage.stats()
        self.assertEqual(stats["total_organized_files"], 2)

    def test_sample_inbox_processing(self):
        # Test copying examples to inbox and organizing
        examples_inbox = Path(__file__).resolve().parent.parent / "examples" / "inbox"
        if examples_inbox.exists():
            for f in examples_inbox.iterdir():
                if f.is_file():
                    shutil.copy(str(f), str(self.config.inbox_dir / f.name))
            res = self.tidier.scan_and_tidy(dry_run=False)
            self.assertTrue(len(res) > 0)
            for item in res:
                self.assertIn("category", item)
                self.assertIn("summary", item)

if __name__ == "__main__":
    unittest.main()
