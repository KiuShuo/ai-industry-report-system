from typing import List, Dict


class AnalysisPipeline:
    def run(self, raw_items: List[Dict[str, str]]) -> List[Dict[str, str]]:
        results: List[Dict[str, str]] = []
        for item in raw_items:
            results.append({
                "title": item.get("title", ""),
                "category": item.get("category", "general"),
                "signalScore": "medium",
                "summary": item.get("summary", ""),
            })
        return results
