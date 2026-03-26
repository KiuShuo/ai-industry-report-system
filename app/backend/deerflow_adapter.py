from typing import Dict, Any


class DeerFlowAdapter:
    def __init__(self, endpoint: str = "", api_key: str = ""):
        self.endpoint = endpoint
        self.api_key = api_key

    def is_configured(self) -> bool:
        return bool(self.endpoint)

    def run_research(self, topic: str, time_range: str) -> Dict[str, Any]:
        if not self.is_configured():
            return {
                "status": "stub",
                "topic": topic,
                "timeRange": time_range,
                "message": "DeerFlow endpoint not configured yet.",
            }
        return {
            "status": "connected",
            "topic": topic,
            "timeRange": time_range,
            "message": "DeerFlow integration placeholder response.",
        }
