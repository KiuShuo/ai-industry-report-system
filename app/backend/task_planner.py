from typing import Dict, List


class TaskPlanner:
    def build_plan(self, topic: str, time_range: str) -> List[Dict[str, str]]:
        return [
            {"name": "collect_sources", "topic": topic, "timeRange": time_range},
            {"name": "group_signals", "topic": topic, "timeRange": time_range},
            {"name": "generate_report", "topic": topic, "timeRange": time_range},
        ]
