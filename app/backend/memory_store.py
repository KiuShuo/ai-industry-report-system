from typing import Dict, List


class AgentMemoryStore:
    def __init__(self):
        self.history: List[Dict[str, str]] = []

    def add(self, item: Dict[str, str]):
        self.history.append(item)

    def query(self, topic: str) -> List[Dict[str, str]]:
        return [h for h in self.history if topic.lower() in h.get("topic", "").lower()]

    def all(self) -> List[Dict[str, str]]:
        return self.history
