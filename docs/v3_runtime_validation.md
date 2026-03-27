# V3 Runtime Validation Guide

## Goal
Validate the DeerFlow-aware V3 backend before and after connecting a real DeerFlow runtime.

## Start V3
```bash
docker compose -f docker-compose.v3.yml up
```

## Required Variables
- `TAVILY_API_KEY`
- `DEEPSEEK_API_KEY`
- `DEERFLOW_BASE_URL` (optional before real DeerFlow is connected)
- `DEERFLOW_API_KEY`
- `PREFER_DEERFLOW`

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

## Expected Signals
- `runtimeConfigured=true` means DeerFlow base URL exists.
- `preferredMode=deerflow` means system intends to route through DeerFlow.
- If DeerFlow is unavailable, investigate runtime endpoint format and response shape.

## Frontend Helpers
- `frontend/runtime-status-v3.html`
- `frontend/report.html`
- `frontend/index.html`
