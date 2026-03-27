# AGENTS.md

## Project Identity
This repository is an AI industry research and report generation system evolving from a Demo V1 into a DeerFlow-enabled V2/V3 architecture.

## Primary Goal
Build an AI Agent product that can:
- accept an industry topic and time range,
- collect signals from live web sources,
- analyze them with an LLM,
- generate structured reports,
- optionally route execution through DeerFlow 2.0.

## Current Architecture
Frontend -> API Gateway / Backend -> Runtime Mode Selector ->
- local chain: Tavily -> AnalysisPipeline -> DeepSeek -> Report
- deerflow chain: DeerFlow runtime client -> skill -> mapped report result

## Important Backend Entry Points
- `app/backend/mvp_main.py`: early MVP backend
- `app/backend/mvp_main_v2.py`: DeerFlow-aware backend
- `app/backend/mvp_main_v3.py`: DeerFlow-aware backend with status probe and result mapper

## Preferred Direction
Prefer continuing from V3 and use V3 as the reference backend for future work.

## Important Modules
- `tavily_connector.py`: live web search
- `deepseek_connector.py`: LLM summarization
- `live_report_service.py`: first live chain
- `live_report_service_v2.py`: local/deerflow dual-mode service
- `deerflow_runtime_client.py`: DeerFlow runtime client skeleton
- `deerflow_result_mapper.py`: maps DeerFlow output back to report storage
- `deerflow_status.py`: runtime status probe
- `runtime_mode_selector.py`: decides whether to use DeerFlow or local chain
- `settings.py`: unified env var management

## Environment Variables
Never hardcode secrets in source code.
Use environment variables only:
- `TAVILY_API_KEY`
- `DEEPSEEK_API_KEY`
- `DEERFLOW_BASE_URL`
- `DEERFLOW_API_KEY`
- `PREFER_DEERFLOW`

## Runtime Behavior
- If `PREFER_DEERFLOW=true` and `DEERFLOW_BASE_URL` is set, prefer DeerFlow.
- Otherwise fall back to the local chain.

## Frontend Files
- `frontend/index.html`: topic input demo page
- `frontend/report.html`: report viewer page
- `frontend/runtime-status.html`: runtime status page

## Docker Runtime Files
- `docker-compose.demo.yml`: Demo V1 runtime
- `docker-compose.v2.yml`: V2/V3 runtime with env vars for Tavily / DeepSeek / DeerFlow

## What Codex Should Focus On Next
1. Treat V3 as the main backend candidate.
2. Wire `docker-compose.v2.yml` or a new compose file to launch V3 by default.
3. Connect V3 health and runtime status into frontend status visualization if useful.
4. Validate the real DeerFlow runtime call shape and update `deerflow_runtime_client.py` accordingly.
5. Improve `deerflow_result_mapper.py` based on real DeerFlow response structure.
6. Keep our app responsible for task records, report storage, scheduling, and UI.
7. Keep DeerFlow focused on orchestration and execution.

## Coding Guidance
- Keep changes modular.
- Prefer adding new versioned entrypoints rather than breaking working files abruptly.
- Avoid deleting prior versions unless replacement is verified.
- Keep report output structured and business-oriented.

## Product Guidance
This project is not just a demo script. It is intended to evolve into a real AI SaaS product for:
- industry monitoring,
- weekly report generation,
- competitor tracking,
- market research,
- management decision support.
