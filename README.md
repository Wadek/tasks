# Tasks

Simple tasks / reminders app (extracted from waka-net for Frontier demos).

## Run locally

```text
cd app
python server.py
```

Default data file: set `TASKS_DATA` or it uses `../data/tasks.json` when run outside Docker.

## Docker (optional)

```text
docker compose up --build
```

## Frontier

Managed with Frontier push (git frontier gate + OWASP policy V).
