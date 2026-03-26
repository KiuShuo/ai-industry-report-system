from typing import Dict, List


class AgentRuntime:
    def __init__(self):
        self.steps: List[str] = []

    def plan(self, topic: str, time_range: str) -> List[Dict[str, str]]:
        return [
            {"step": "collect", "topic": topic, "timeRange": time_range},
            {"step": "analyze", "topic": topic, "timeRange": time_range},
            {"step": "report", "topic": topic, "timeRange": time_range},
        ]

    def run(self, topic: str, time_range: str) -> Dict[str, object]:
        tasks = self.plan(topic, time_range)
        self.steps = [item["step"] for item in tasks]
        return {
            "topic": topic,
            "timeRange": time_range,
            "steps": self.steps,
            "status": "planned",
        }
