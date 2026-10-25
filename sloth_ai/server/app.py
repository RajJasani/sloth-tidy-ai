"""
Lightweight Zero-Dependency Web Server and REST API for SlothTidy AI.
Provides a modern web UI dashboard and REST endpoints.
"""

import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from pathlib import Path
from typing import Dict, Any
from sloth_ai.config import DEFAULT_CONFIG, SlothConfig
from sloth_ai.core.engine import LocalAIEngine
from sloth_ai.modules.storage import SlothStorage
from sloth_ai.modules.tidier import SlothTidier
from sloth_ai.modules.digest import SlothDigest

STATIC_DIR = Path(__file__).parent / "static"

class SlothRequestHandler(BaseHTTPRequestHandler):
    config = DEFAULT_CONFIG
    engine = LocalAIEngine(config)
    storage = SlothStorage(config)
    tidier = SlothTidier(engine, storage, config)
    digest = SlothDigest(engine, storage, config)

    def _send_json(self, status_code: int, data: Any):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, file_path: Path, content_type: str = "text/html"):
        if not file_path.exists():
            self.send_error(404, "File Not Found")
            return
        content = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path in ("/", "/index.html"):
            return self._send_file(STATIC_DIR / "index.html", "text/html")
        
        if path == "/api/status":
            health = self.engine.check_health()
            stats = self.storage.stats()
            return self._send_json(200, {**health, **stats})

        if path == "/api/files":
            files = self.storage.list_files(limit=50)
            return self._send_json(200, {"files": files})

        if path == "/api/digests":
            digests = self.storage.list_digests(limit=20)
            return self._send_json(200, {"digests": digests})

        self.send_error(404, "Endpoint Not Found")

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
        
        try:
            body = json.loads(post_data) if post_data.strip() else {}
        except Exception:
            body = {}

        if path == "/api/tidy":
            folder = body.get("folder")
            dry_run = body.get("dry_run", False)
            source_path = Path(folder) if folder else None
            results = self.tidier.scan_and_tidy(source_dir=source_path, dry_run=dry_run)
            return self._send_json(200, {"organized": results, "count": len(results)})

        if path == "/api/digest":
            text = body.get("text", "")
            title = body.get("title")
            res = self.digest.generate_digest_from_text(text, title)
            return self._send_json(200, res)

        self.send_error(404, "Endpoint Not Found")

    def log_message(self, format, *args):
        # Clean logging
        pass

def run_server(host: str = None, port: int = None):
    cfg = DEFAULT_CONFIG
    h = host or cfg.host
    p = port or cfg.port
    server = HTTPServer((h, p), SlothRequestHandler)
    print(f"🦥 SlothTidy AI server running at http://{h}:{p}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping SlothTidy AI server...")
        server.server_close()
