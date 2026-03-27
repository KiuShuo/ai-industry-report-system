# Environment Variables Example

Copy [.env.example](/Users/liushuo/Documents/cos-out/hangzu/ai-industry-report-system/.env.example) to `.env`, then fill in your real values before running the V3 backend via `docker-compose.v2.yml`.

```bash
cp .env.example .env
```

```bash
TAVILY_API_KEY=your_tavily_key
DEEPSEEK_API_KEY=your_deepseek_key
DEERFLOW_BASE_URL=http://your-deerflow-runtime
DEERFLOW_API_KEY=your_deerflow_api_key
DEERFLOW_SKILL_NAME=industry-report-skill
PREFER_DEERFLOW=true
```

## Mode Selection
- If `PREFER_DEERFLOW=true` and `DEERFLOW_BASE_URL` is set, the system prefers DeerFlow execution.
- Otherwise the system falls back to the local chain: Tavily + AnalysisPipeline + DeepSeek.
- Use `http://localhost:8000/api/runtime/status` to verify `preferredMode`, `effectiveMode`, and whether fallback is active.
- `.env` is now ignored by Git via [.gitignore](/Users/liushuo/Documents/cos-out/hangzu/ai-industry-report-system/.gitignore), so local secrets will not be committed by default.
