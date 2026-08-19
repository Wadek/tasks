"""Layer B — browser smoke (Playwright): end-user flows still work."""
from __future__ import annotations

import os
import re

import pytest

pytest.importorskip("playwright")
from playwright.sync_api import expect


def test_ui_add_toggle_edit_delete_search(tasks_base, page):
    # Prefer explicit gateway URL if set; else ephemeral test server (no token needed).
    url = os.environ.get("TASKS_E2E_BASE", tasks_base)
    page.goto(url if "://" in url and "?" in url else url.rstrip("/") + "/")
    expect(page.locator("h1")).to_have_text(re.compile("Tasks", re.I))

    # Add
    page.fill("#new-title", "browser-smoke-1")
    page.fill("#new-notes", "hello")
    page.click("#add-btn")
    expect(page.locator(".task-title", has_text="browser-smoke-1")).to_be_visible()

    # Search
    page.fill("#search", "browser-smoke")
    expect(page.locator(".task-title", has_text="browser-smoke-1")).to_be_visible()
    page.fill("#search", "no-match-zzz")
    expect(page.locator("#empty")).to_be_visible()
    page.fill("#search", "")

    # Toggle via checkbox
    task = page.locator(".task", has_text="browser-smoke-1")
    task.locator('input[type="checkbox"]').check()
    expect(task).to_have_class(re.compile(r"completed"))

    # Edit
    task.locator("button", has_text="Edit").click()
    page.fill("#edit-title", "browser-smoke-1-edited")
    page.click("#save-edit")
    expect(page.locator(".task-title", has_text="browser-smoke-1-edited")).to_be_visible()

    # Delete
    page.locator(".task", has_text="browser-smoke-1-edited").locator(
        "button", has_text="Edit"
    ).click()
    page.once("dialog", lambda d: d.accept())
    page.click("#delete-edit")
    expect(page.locator(".task-title", has_text="browser-smoke-1-edited")).to_have_count(0)
