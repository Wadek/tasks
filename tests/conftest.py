"""Shared fixtures: ephemeral tasks server for equivalence + browser tests."""
from __future__ import annotations

import os
import socket
import sys
import threading
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "app"
sys.path.insert(0, str(APP_DIR))


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="session")
def tasks_server(tmp_path_factory):
    """Start ThreadedServer on a free port with temp data file."""
    import server as srv

    data_dir = tmp_path_factory.mktemp("tasks-data")
    data_file = data_dir / "tasks.json"
    data_file.write_text("[]", encoding="utf-8")

    os.environ["TASKS_DATA_FILE"] = str(data_file)
    os.environ["TASKS_APP_DIR"] = str(APP_DIR)

    # Re-bind module paths for this process
    srv.DATA_FILE = Path(data_file)
    srv.APP_DIR = Path(APP_DIR)
    srv.tasks_cache = []
    srv.tasks_by_id = {}
    srv.load_tasks()
    if hasattr(srv, "load_static_cache"):
        srv.load_static_cache()

    port = _free_port()
    httpd = srv.ThreadedServer(("127.0.0.1", port), srv.TasksHandler)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    base = f"http://127.0.0.1:{port}"
    # wait until up
    import urllib.request

    for _ in range(50):
        try:
            urllib.request.urlopen(base + "/api/tasks", timeout=0.2)
            break
        except Exception:
            time.sleep(0.05)
    yield {"base": base, "data_file": data_file, "app_dir": APP_DIR, "httpd": httpd}
    httpd.shutdown()


@pytest.fixture
def tasks_base(tasks_server):
    """App URL for tests. Named tasks_base to avoid clashing with pytest-base-url."""
    return tasks_server["base"]
