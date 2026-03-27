# Codex Handoff

## 1. Project Background
This project started as an AI application for "industry dynamics query and report generation".
It has since evolved into an AI Agent oriented product prototype with:
- backend service,
- frontend demo pages,
- Docker runtime,
- Tavily integration,
- DeepSeek integration,
- DeerFlow 2.0 integration preparation.

The product goal is to support real business scenarios such as:
- industry monitoring,
- weekly reports,
- market research,
- competitor tracking,
- management decision support.

## 2. Current State
The repository already contains:
- early MVP backend,
- DeerFlow-aware V2 backend,
- DeerFlow-aware V3 backend,
- frontend demo pages,
- local and DeerFlow-capable execution chain,
- docs and runtime guides.

This is no longer a blank prototype. It is a structured product prototype.

## 3. Technical Stack
- Backend: FastAPI
- Frontend: simple static HTML demo pages
- Search: Tavily
- LLM: DeepSeek
- Optional orchestration runtime: DeerFlow 2.0
- Runtime packaging: Docker Compose

## 4. Main Execution Modes
### Local Chain
Tavily -> AnalysisPipeline -> DeepSeek -> Markdown/HTML report

### DeerFlow Chain
Task -> DeerFlow runtime client -> skill -> DeerFlow result mapper -> report storage

## 5. Important Files
### Backend entrypoints
- `app/backend/mvp_main.py`
- `app/backend/mvp_main_v2.py`
- `app/backend/mvp_main_v3.py`

### Core runtime modules
- `app/backend/tavily_connector.py`
- `app/backend/deepseek_connector.py`
- `app/backend/live_report_service.py`
- `app/backend/live_report_service_v2.py`
- `app/backend/deerflow_runtime_client.py`
- `app/backend/deerflow_result_mapper.py`
- `app/backend/deerflow_status.py`
- `app/backend/runtime_mode_selector.py`
- `app/backend/settings.py`

### Frontend
- `frontend/index.html`
- `frontend/report.html`
- `frontend/runtime-status.html`

### Runtime files
- `docker-compose.demo.yml`
- `docker-compose.v2.yml`

## 6. Preferred Development Baseline
Use **V3** as the main reference backend for future development.
Do not treat the earliest MVP files as the main target.

## 7. Business / Architecture Principle
Keep responsibilities separated:

### Our application should own
- task records,
- scheduling,
- report metadata,
- stored report artifacts,
- UI / frontend,
- product workflows.

### DeerFlow should own
- execution orchestration,
- multi-step planning,
- research runtime,
- tool use,
- skill execution.

This split is intentional and should be preserved.

## 8. Environment Variables
Do not hardcode secrets.
Use environment variables only:
- `TAVILY_API_KEY`
- `DEEPSEEK_API_KEY`
- `DEERFLOW_BASE_URL`
- `DEERFLOW_API_KEY`
- `PREFER_DEERFLOW`

## 9. What Is Not Finished Yet
These are the main unfinished items:
1. Real DeerFlow runtime endpoint validation
2. Real DeerFlow result shape confirmation
3. Make V3 the default runtime in Docker startup
4. Improve frontend status page to show DeerFlow/local mode clearly
5. Improve report rendering / storage quality
6. Potentially migrate frontend to a more formal app framework later

## 10. Recommended Next Steps for Codex
### Priority A
- Make V3 the default active runtime path
- Update compose startup to use V3
- Add a clearer runtime status API contract if needed

### Priority B
- Verify real DeerFlow runtime call shape
- Update `deerflow_runtime_client.py`
- Update `deerflow_result_mapper.py`

### Priority C
- Improve frontend product experience
- Render report HTML more clearly
- Show execution mode on frontend

## 11. Engineering Guidance
- Prefer modular edits.
- Prefer extending V3 rather than breaking older files.
- Keep local fallback working even if DeerFlow is unavailable.
- Treat this repository as a product prototype, not a throwaway demo.

## 12. Expected Outcome
Codex should continue this project toward:
- a runnable V3 default backend,
- a DeerFlow-connected execution path,
- a more product-like demo,
- a future transition toward a real AI SaaS product.
