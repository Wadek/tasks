# Tasks

Simple tasks / reminders app (live habitat: `D:\wakalabs\tasks`, remote: `github.com/Wadek/tasks`).

## Run locally

```text
cd app
set TASKS_APP_DIR=%CD%
set TASKS_DATA_FILE=..\data\tasks.json
python server.py
```

## Docker (waka-net)

```text
docker compose up -d
```

Joins external network `waka-net`; UI at gateway `tasks.wakalabs.net`.

## Tests (Optimize verification)

See Frontier Ship [`english/O_VERIFY.md`](https://github.com/Wadek/frontier-ship/blob/main/english/O_VERIFY.md).

```text
pip install -r requirements-dev.txt
playwright install chromium
pytest -v --tb=short
```

- **Layer A:** `tests/test_api_equivalence.py` — API + static bytes == disk  
- **Layer B:** `tests/test_browser_smoke.py` — Playwright add/toggle/edit/delete/search  
- **GitHub Actions:** `.github/workflows/verify.yml` runs the same suite on every PR (visible checks)

Optional: `TASKS_E2E_BASE=https://tasks.wakalabs.net?token=…` for gateway browser runs.

Always prefer **`-v`** so humans/agents see which tests passed.

## Frontier

```text
frontier learn | guard | optimize
frontier optimize pr-body Opt-00N
```

