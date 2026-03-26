# AI Industry Report Agent (V1 Demo)

## Overview
AI-driven industry intelligence and report generation platform based on Agent architecture.

## Core Capabilities
- Multi-step agent workflow (plan → execute → analyze → report)
- Industry signal processing pipeline
- Report generation (Markdown → HTML ready)
- Memory-based analysis
- Frontend demo interaction
- Docker-based quick start

## Architecture
Frontend → API Gateway → Agent Runtime → Planner / Executor / Analysis → Memory → Report Engine → Renderer

## Quick Start
```bash
docker compose -f docker-compose.demo.yml up
```

## Demo Flow
1. Input industry topic
2. Generate task
3. Query report

## Status
Demo V1 Completed

## Next Step
- DeerFlow integration
- Real data connectors
- SaaS evolution
