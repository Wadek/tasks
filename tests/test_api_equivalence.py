"""Layer A — equivalence: API contracts + static bytes match disk."""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path


def _req(base: str, method: str, path: str, body: dict | None = None):
    data = None
    headers = {}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    r = urllib.request.Request(base + path, data=data, headers=headers, method=method)
    with urllib.request.urlopen(r, timeout=5) as resp:
        raw = resp.read()
        return resp.status, raw, dict(resp.headers)


def test_list_empty(tasks_base):
    status, raw, _ = _req(tasks_base, "GET", "/api/tasks")
    assert status == 200
    data = json.loads(raw)
    assert "tasks" in data
    assert isinstance(data["tasks"], list)


def test_create_toggle_update_delete_roundtrip(tasks_base):
    status, raw, _ = _req(
        tasks_base, "POST", "/api/tasks", {"title": "equiv-1", "due": "2099-01-01", "notes": "n"}
    )
    assert status == 200
    task = json.loads(raw)
    assert task["title"] == "equiv-1"
    assert task["completed"] is False
    tid = task["id"]

    status, raw, _ = _req(tasks_base, "POST", f"/api/tasks/{tid}/toggle", {})
    assert status == 200
    toggled = json.loads(raw)
    assert toggled["id"] == tid
    assert toggled["completed"] is True

    status, raw, _ = _req(
        tasks_base, "POST", f"/api/tasks/{tid}", {"title": "equiv-1b", "notes": "n2"}
    )
    assert status == 200
    updated = json.loads(raw)
    assert updated["title"] == "equiv-1b"
    assert updated["notes"] == "n2"
    assert updated["completed"] is True

    status, raw, _ = _req(tasks_base, "DELETE", f"/api/tasks/{tid}")
    assert status == 200
    assert json.loads(raw) == {"ok": True}

    status, raw, _ = _req(tasks_base, "GET", "/api/tasks")
    ids = [t["id"] for t in json.loads(raw)["tasks"]]
    assert tid not in ids


def test_static_index_and_js_match_disk(tasks_base, tasks_server):
    """Opt-002 equivalence: served bytes identical to files on disk."""
    app_dir: Path = tasks_server["app_dir"]
    for url_path, filename in (("/", "index.html"), ("/main.js", "main.js")):
        disk = (app_dir / filename).read_bytes()
        status, raw, headers = _req(tasks_base, "GET", url_path)
        assert status == 200
        assert raw == disk, f"{filename} body != disk"
        cl = headers.get("Content-Length")
        if cl is not None:
            assert int(cl) == len(disk)


def test_static_still_matches_after_repeated_gets(tasks_base, tasks_server):
    """Cache must not drift: many GETs still equal disk."""
    app_dir: Path = tasks_server["app_dir"]
    disk = (app_dir / "index.html").read_bytes()
    for _ in range(20):
        status, raw, _ = _req(tasks_base, "GET", "/")
        assert status == 200
        assert raw == disk
