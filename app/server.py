#!/usr/bin/env python3
"""
Simple tasks / reminders app.
- List, add, edit, toggle, delete tasks
- Due dates for reminders
- Persisted to JSON
- Same token auth style as books (handled at gateway)
"""

import os
import json
import uuid
import datetime
import urllib.parse
from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn

DATA_FILE = Path("/data/tasks.json")
PORT = 8080

# tasks_cache preserves JSON array order; tasks_by_id is O(1) lookup (Opt-001).
tasks_cache = []
tasks_by_id = {}

def rebuild_index():
    """Rebuild id -> task map from tasks_cache. Call after any list replace."""
    global tasks_by_id
    tasks_by_id = {t["id"]: t for t in tasks_cache if isinstance(t, dict) and "id" in t}

def load_tasks():
    global tasks_cache
    if DATA_FILE.exists():
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                tasks_cache = json.load(f)
        except Exception:
            tasks_cache = []
    else:
        tasks_cache = []
    if not isinstance(tasks_cache, list):
        tasks_cache = []
    rebuild_index()
    # Ensure data dir
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)

def save_tasks():
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(tasks_cache, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print("Save error:", e)

def now_iso():
    return datetime.datetime.utcnow().isoformat() + "Z"

class TasksHandler(BaseHTTPRequestHandler):
    def _send_headers(self, code=200, ctype="application/json", length=None, no_cache=False):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        if length:
            self.send_header("Content-Length", str(length))
        if no_cache:
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if path == "/":
            self.serve_static("index.html", "text/html; charset=utf-8")
            return

        if path.startswith("/shared/"):
            real = Path("/shared") / path[8:]
            if real.exists():
                self.serve_path(real)
                return

        if path == "/api/tasks":
            # Optional filter
            q = query.get("q", [""])[0].lower().strip()
            results = tasks_cache
            if q:
                results = [
                    t for t in tasks_cache
                    if q in t.get("title", "").lower()
                    or q in (t.get("notes") or "").lower()
                ]
            # Sort: incomplete first by due (nulls last), then completed
            def sort_key(t):
                due = t.get("due") or "9999-99-99"
                completed = 1 if t.get("completed") else 0
                return (completed, due)
            results = sorted(results, key=sort_key)
            body = json.dumps({"tasks": results}).encode("utf-8")
            self._send_headers(200, "application/json", len(body), no_cache=True)
            self.wfile.write(body)
            return

        if path.startswith("/static/") or path == "/main.js":
            candidate = Path("/app") / path.lstrip("/")
            if candidate.exists():
                ctype = "application/octet-stream"
                if candidate.suffix == ".js":
                    ctype = "text/javascript; charset=utf-8"
                elif candidate.suffix == ".css":
                    ctype = "text/css; charset=utf-8"
                self.serve_path(candidate, ctype)
                return

        self.send_error(404)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        length = int(self.headers.get("Content-Length", 0) or 0)
        body = self.rfile.read(length)
        try:
            data = json.loads(body) if body else {}
        except:
            data = {}

        if path == "/api/tasks":
            # Create
            title = (data.get("title") or "").strip()
            if not title:
                self._send_headers(400)
                self.wfile.write(b'{"error":"title required"}')
                return

            task = {
                "id": str(uuid.uuid4()),
                "title": title,
                "due": data.get("due") or None,
                "notes": (data.get("notes") or "").strip() or None,
                "completed": False,
                "created": now_iso(),
            }
            tasks_cache.append(task)
            tasks_by_id[task["id"]] = task
            save_tasks()
            self._send_headers(200)
            self.wfile.write(json.dumps(task).encode("utf-8"))
            return

        if path.startswith("/api/tasks/") and path.endswith("/toggle"):
            tid = path.split("/api/tasks/")[1].split("/toggle")[0]
            t = tasks_by_id.get(tid)
            if t is None:
                self.send_error(404)
                return
            t["completed"] = not t.get("completed", False)
            save_tasks()
            self._send_headers(200)
            self.wfile.write(json.dumps(t).encode("utf-8"))
            return

        if path.startswith("/api/tasks/") and not path.endswith(("/toggle",)):
            # Update
            tid = path.split("/api/tasks/")[1]
            t = tasks_by_id.get(tid)
            if t is None:
                self.send_error(404)
                return
            if "title" in data:
                t["title"] = (data["title"] or "").strip()
            if "due" in data:
                t["due"] = data["due"] or None
            if "notes" in data:
                t["notes"] = (data.get("notes") or "").strip() or None
            if "completed" in data:
                t["completed"] = bool(data["completed"])
            save_tasks()
            self._send_headers(200)
            self.wfile.write(json.dumps(t).encode("utf-8"))
            return

        self.send_error(405)

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path.startswith("/api/tasks/"):
            tid = path.split("/api/tasks/")[1]
            global tasks_cache
            if tid not in tasks_by_id:
                self.send_error(404)
                return
            tasks_cache = [t for t in tasks_cache if t.get("id") != tid]
            tasks_by_id.pop(tid, None)
            save_tasks()
            self._send_headers(200)
            self.wfile.write(b'{"ok":true}')
            return

        self.send_error(405)

    def serve_static(self, name, ctype):
        p = Path("/app") / name
        if p.exists():
            data = p.read_bytes()
            self._send_headers(200, ctype, len(data), no_cache=True)
            self.wfile.write(data)
        else:
            self.send_error(404)

    def serve_path(self, p, ctype="application/octet-stream"):
        data = p.read_bytes()
        self._send_headers(200, ctype, len(data))
        self.wfile.write(data)

class ThreadedServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

if __name__ == "__main__":
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    load_tasks()
    print(f"tasks server ready — {len(tasks_cache)} tasks")
    httpd = ThreadedServer(("", PORT), TasksHandler)
    print(f"listening on :{PORT}")
    httpd.serve_forever()
