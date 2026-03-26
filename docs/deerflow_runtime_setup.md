# DeerFlow Runtime Setup Guide

## Recommended Role Split
- Our app: task records, scheduling, report storage, UI
- DeerFlow: orchestration, research execution, multi-step planning

## Required Environment Variables
- DEERFLOW_BASE_URL
- DEERFLOW_API_KEY
- PREFER_DEERFLOW=true
- TAVILY_API_KEY
- DEEPSEEK_API_KEY

## Recommended Runtime Pattern
1. User submits an industry topic.
2. Our API records the task.
3. LiveReportServiceV2 chooses execution mode.
4. If DeerFlow is configured, route to DeerFlow runtime skill.
5. Otherwise, fallback to local chain.
6. Persist report artifacts back into our application.

## Why This Pattern
This keeps product state in our system and uses DeerFlow as the execution engine, which matches DeerFlow's strengths in planning, tool use, and modular skills.
