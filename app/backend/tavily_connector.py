import os
from typing import Dict, List, Optional

from http_client import request_json


class TavilyConnector:
    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.tavily.com/search"):
        self.api_key = api_key or os.getenv("TAVILY_API_KEY", "")
        self.base_url = base_url

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def search(self, topic: str, time_range: str = "7d", max_results: int = 5) -> List[Dict[str, str]]:
        if not self.is_configured():
            return [
                {
                    "title": f"{topic} Tavily connector not configured",
                    "summary": "Set TAVILY_API_KEY in environment variables to enable live search.",
                    "source": "tavily",
                    "category": "search",
                    "url": "",
                }
            ]

        payload = {
            "api_key": self.api_key,
            "query": f"{topic} latest industry updates in the last {time_range}",
            "search_depth": "advanced",
            "max_results": max_results,
            "include_answer": False,
            "include_raw_content": False,
        }

        response = request_json("POST", self.base_url, json_body=payload, timeout=30)
        response.raise_for_status()
        data = response.json()

        items: List[Dict[str, str]] = []
        for result in data.get("results", []):
            items.append(
                {
                    "title": result.get("title", ""),
                    "summary": result.get("content", ""),
                    "source": result.get("url", "tavily"),
                    "category": "search",
                    "url": result.get("url", ""),
                }
            )
        return items
