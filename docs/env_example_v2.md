# Environment Variables Example

Set these variables before running the V2 backend.

```bash
export TAVILY_API_KEY=your_tavily_key
export DEEPSEEK_API_KEY=your_deepseek_key
export DEERFLOW_BASE_URL=http://your-deerflow-runtime
export DEERFLOW_API_KEY=your_deerflow_api_key
export PREFER_DEERFLOW=true
```

## Mode Selection
- If `PREFER_DEERFLOW=true` and `DEERFLOW_BASE_URL` is set, the system prefers DeerFlow execution.
- Otherwise the system falls back to the local chain: Tavily + AnalysisPipeline + DeepSeek.
