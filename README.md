# AI Industry Report System

AI‑driven industry intelligence and report generation platform.

## Overview
This project aims to build an automated AI system that can:
- Monitor industry dynamics
- Generate structured analytical reports
- Support business decision making

## Current Progress
- Cloud server deployed
- Infrastructure ready (Docker / PostgreSQL / Redis / MinIO)
- Backend MVP running with FastAPI
- V3 runtime path available with DeerFlow-aware fallback

## Recommended Start
Use the V3 stack as the default baseline:

```bash
docker compose -f docker-compose.v2.yml up
```

Then open:
- `http://localhost:8080/index.html`
- `http://localhost:8080/runtime-status.html`

## Runtime Notes
- `PREFER_DEERFLOW=true` and `DEERFLOW_BASE_URL` set: prefer DeerFlow.
- DeerFlow unavailable or returns no usable report artifact: fallback to local chain.
- V3 now surfaces DeerFlow probe endpoint, fallback reason, and async poll metadata in task/report views.

## Roadmap
- Validate the real DeerFlow runtime call shape
- Confirm real DeerFlow result payload structure
- Build a richer frontend dashboard
- Implement scheduled reports

## Tech Stack
- FastAPI
- Docker
- PostgreSQL
- Redis
- MinIO

More documentation coming soon.
