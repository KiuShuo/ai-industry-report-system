# V2 Startup Guide

## Goal
Start the DeerFlow-aware V2 backend and the demo frontend.

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
- If DeerFlow is configured and preferred, the V2 backend routes tasks to DeerFlow.
- Otherwise the V2 backend falls back to the local chain using Tavily and DeepSeek.

## Recommended Verification
1. Start with `PREFER_DEERFLOW=false` and verify the local chain.
2. Then set `DEERFLOW_BASE_URL` and `PREFER_DEERFLOW=true`.
3. Submit a task and verify the returned report mode.
