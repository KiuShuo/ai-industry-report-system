from typing import List, Dict


class AnalysisPipeline:
    def run(self, raw_items: List[Dict[str, str]]) -> List[Dict[str, str]]:
        results: List[Dict[str, str]] = []
        for index, item in enumerate(raw_items, start=1):
            results.append({
                "sourceId": item.get("sourceId", f"S{index}"),
                "title": item.get("title", ""),
                "category": item.get("category", "general"),
                "signalScore": "medium",
                "summary": item.get("summary", ""),
                "rawContent": item.get("rawContent", ""),
                "source": item.get("source", ""),
                "url": item.get("url", ""),
                "publishedDate": item.get("publishedDate", ""),
                "score": item.get("score", ""),
                "favicon": item.get("favicon", ""),
                "searchProfile": item.get("searchProfile", ""),
            })
        return results
