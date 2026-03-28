# Environment Variables Example

Copy [.env.example](/Users/liushuo/Documents/cos-out/hangzu/ai-industry-report-system/.env.example) to `.env`, then fill in your real values before running the V3 backend via `docker-compose.v2.yml`.

```bash
cp .env.example .env
```

```bash
TAVILY_API_KEY=your_tavily_key
SEARCH_PROFILE=auto
TAVILY_TOPIC=news
TAVILY_SEARCH_DEPTH=advanced
TAVILY_INCLUDE_RAW_CONTENT=markdown
TAVILY_INCLUDE_FAVICON=true
TAVILY_INCLUDE_DOMAINS=
TAVILY_EXCLUDE_DOMAINS=baike.baidu.com,linkedin.com
TAVILY_AUTO_PARAMETERS=false
TAVILY_CHUNKS_PER_SOURCE=3
DEEPSEEK_API_KEY=your_deepseek_key
DEERFLOW_BASE_URL=http://your-deerflow-runtime
DEERFLOW_API_KEY=your_deerflow_api_key
DEERFLOW_SKILL_NAME=industry-report-skill
PREFER_DEERFLOW=true
```

## Mode Selection
- If `PREFER_DEERFLOW=true` and `DEERFLOW_BASE_URL` is set, the system prefers DeerFlow execution.
- Otherwise the system falls back to the local chain: Tavily + AnalysisPipeline + DeepSeek.
- `SEARCH_PROFILE=auto` means the system auto-selects a built-in search profile based on the topic.
- You can force a profile later, for example `shipping-finance-leasing`, without changing application code.
- `TAVILY_INCLUDE_DOMAINS` and `TAVILY_EXCLUDE_DOMAINS` can be used to control source quality.
- `TAVILY_INCLUDE_RAW_CONTENT=markdown` helps the report use stronger evidence than short search snippets.
- Use `http://localhost:8000/api/runtime/status` to verify `preferredMode`, `effectiveMode`, and whether fallback is active.
- `.env` is now ignored by Git via [.gitignore](/Users/liushuo/Documents/cos-out/hangzu/ai-industry-report-system/.gitignore), so local secrets will not be committed by default.
