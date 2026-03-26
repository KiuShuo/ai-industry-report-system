from typing import List, Dict


class MockIndustryDataSource:
    def search(self, topic: str, time_range: str) -> List[Dict[str, str]]:
        return [
            {
                "title": f"{topic} market update",
                "summary": f"Mock data for topic={topic}, range={time_range}",
                "source": "mock-source",
                "category": "market",
            },
            {
                "title": f"{topic} policy signal",
                "summary": f"Policy tracking placeholder for {topic}",
                "source": "mock-source",
                "category": "policy",
            },
        ]
