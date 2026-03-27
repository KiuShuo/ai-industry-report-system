# V3 Runtime Validation Guide

## Goal
Validate the DeerFlow-aware V3 backend before and after connecting a real DeerFlow runtime.

## Start V3
```bash
docker compose -f docker-compose.v2.yml up
```

`docker-compose.v3.yml` remains available as a compatibility alias, but `docker-compose.v2.yml` should be treated as the default V3 startup entry.

## Required Variables
- `TAVILY_API_KEY`
- `DEEPSEEK_API_KEY`
- `DEERFLOW_BASE_URL` (optional before real DeerFlow is connected)
- `DEERFLOW_API_KEY`
- `DEERFLOW_SKILL_NAME`
- `PREFER_DEERFLOW`
- `DEERFLOW_POLL_INTERVAL_SECONDS`
- `DEERFLOW_POLL_MAX_ATTEMPTS`

## Validation Steps
### Phase 1: Local Mode
1. Set `PREFER_DEERFLOW=false`
2. Start V3
3. Open `/health`
4. Open `/api/runtime/status`
5. Create a task and verify report mode is `local`

### Phase 2: DeerFlow Preferred Mode
1. Set `PREFER_DEERFLOW=true`
2. Set `DEERFLOW_BASE_URL`
3. Restart V3
4. Check `/health`
5. Check `/api/runtime/status`
6. Create a task and verify report mode is `deerflow`
7. If DeerFlow returns an async run, verify task/report payloads include `deerflow.endpoint` and `deerflow.pollAttempts`

## Expected Signals
- `runtimeConfigured=true` means DeerFlow base URL exists.
- `preferredMode=deerflow` means system intends to route through DeerFlow.
- `probeEndpoint` tells you which DeerFlow health path was actually reachable.
- `deerflow.pollAttempts` shows how many poll cycles were needed before a final result was received.
- If DeerFlow is unavailable, investigate runtime endpoint format and response shape.

## Frontend Helpers
- `frontend/runtime-status.html`
- `frontend/report.html`
- `frontend/index.html`
