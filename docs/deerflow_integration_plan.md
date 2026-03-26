# DeerFlow 2.0 Integration Plan

## Goal
Integrate DeerFlow 2.0 as the execution and orchestration layer for industry research tasks.

## Planned Architecture
Frontend -> API Gateway -> Our Task API -> DeerFlow Adapter -> DeerFlow Runtime -> Tavily / DeepSeek / Report Output

## Best Practice Directions
1. Keep DeerFlow as the orchestration runtime instead of mixing business state into DeerFlow.
2. Use skills for domain workflows such as industry-news, weekly-report, competitor-tracking.
3. Keep secrets in environment variables only.
4. Run DeerFlow in isolated sandbox mode and mount only required directories.
5. Keep our application responsible for task records, report metadata, user access, and scheduling.

## Next Development Tasks
- Replace current stub adapter with HTTP based DeerFlow runtime client.
- Add skill definitions for industry report generation.
- Route long-running research tasks through DeerFlow.
- Preserve report artifacts in our app while DeerFlow handles execution.
