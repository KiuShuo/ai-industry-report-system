from typing import Dict, List


class TaskExecutor:
    def execute(self, steps: List[Dict[str, str]]) -> List[Dict[str, str]]:
        results: List[Dict[str, str]] = []
        for step in steps:
            results.append({
                "name": step.get("name", "unknown"),
                "status": "done",
                "topic": step.get("topic", ""),
                "timeRange": step.get("timeRange", ""),
            })
        return results
