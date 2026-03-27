# V3 Startup Guide

## Goal
Start the DeerFlow-aware V3 backend and the demo frontend.

## Required Variables
- TAVILY_API_KEY
- DEEPSEEK_API_KEY
- DEERFLOW_BASE_URL (optional for DeerFlow mode)
- DEERFLOW_API_KEY (optional depending on runtime)
- PREFER_DEERFLOW=true or false

## Start With Docker Compose
```bash
docker compose -f docker-compose.v2.yml up
```

## Open
- Frontend: http://localhost:8080
- API docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

## Runtime Behavior
- `docker-compose.v2.yml` now launches `app/backend/mvp_main_v3.py` by default.
- If DeerFlow is configured and preferred, the V3 backend tries DeerFlow first.
- If DeerFlow is unavailable, the request fails, or the result cannot be mapped into a report, V3 falls back to the local chain using Tavily and DeepSeek.

## Recommended Verification
1. Start with `PREFER_DEERFLOW=false` and verify the local chain.
2. Then set `DEERFLOW_BASE_URL` and `PREFER_DEERFLOW=true`.
3. Open `http://localhost:8000/api/runtime/status` and confirm the DeerFlow probe result.
4. Submit a task and verify the returned `mode`, `requestedMode`, and any `fallbackReason`.
