import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from urllib.parse import urlparse

from http_client import request_json
from search_profiles import SearchProfile, resolve_search_profile
from settings import get_settings


class TavilyConnector:
    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.tavily.com/search"):
        self.api_key = api_key or os.getenv("TAVILY_API_KEY", "")
        self.base_url = base_url
        self.settings = get_settings()

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _query_for_topic(self, topic: str, time_range: str, profile: SearchProfile) -> str:
        return f"{topic} {profile.query_hint} in the last {time_range}"

    def _time_filter_payload(self, time_range: str) -> Dict[str, object]:
        normalized = (time_range or "").strip().lower()
        if not normalized:
            return {}

        if normalized.endswith("d") and normalized[:-1].isdigit():
            days = int(normalized[:-1])
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=max(days - 1, 0))
            return {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            }

        mapping = {
            "day": "day",
            "week": "week",
            "month": "month",
            "year": "year",
        }
        if normalized in mapping:
            return {"time_range": mapping[normalized]}

        return {}

    def _source_name(self, url: str) -> str:
        if not url:
            return "tavily"
        parsed = urlparse(url)
        return parsed.netloc or url

    def _effective_include_domains(self, profile: SearchProfile) -> List[str]:
        if self.settings.tavily_include_domains:
            return self.settings.tavily_include_domains
        return profile.include_domains

    def _effective_exclude_domains(self, profile: SearchProfile) -> List[str]:
        combined: List[str] = []
        for item in profile.exclude_domains + self.settings.tavily_exclude_domains:
            if item and item not in combined:
                combined.append(item)
        return combined

    def resolve_profile(self, topic: str) -> SearchProfile:
        return resolve_search_profile(topic, self.settings.search_profile)

    def _build_payload(self, topic: str, time_range: str, max_results: int, profile: SearchProfile) -> Dict[str, object]:
        payload: Dict[str, object] = {
            "query": self._query_for_topic(topic, time_range, profile),
            "topic": profile.tavily_topic or self.settings.tavily_topic,
            "search_depth": self.settings.tavily_search_depth,
            "max_results": max_results,
            "include_answer": self.settings.tavily_include_answer,
            "include_raw_content": self.settings.tavily_include_raw_content,
            "include_favicon": self.settings.tavily_include_favicon,
            "include_images": False,
            "auto_parameters": self.settings.tavily_auto_parameters,
            "include_usage": True,
        }

        if self.settings.tavily_chunks_per_source > 0:
            payload["chunks_per_source"] = self.settings.tavily_chunks_per_source
        include_domains = self._effective_include_domains(profile)
        exclude_domains = self._effective_exclude_domains(profile)
        if include_domains:
            payload["include_domains"] = include_domains
        if exclude_domains:
            payload["exclude_domains"] = exclude_domains
        if self.settings.tavily_country:
            payload["country"] = self.settings.tavily_country

        payload.update(self._time_filter_payload(time_range))
        return payload

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

        profile = self.resolve_profile(topic)
        payload = self._build_payload(topic, time_range, max_results, profile)
        response = request_json("POST", self.base_url, headers=self._headers(), json_body=payload, timeout=30)
        response.raise_for_status()
        data = response.json()

        items: List[Dict[str, str]] = []
        for result in data.get("results", []):
            url = result.get("url", "")
            raw_content = result.get("raw_content", "") or ""
            content = result.get("content", "") or ""
            items.append(
                {
                    "title": result.get("title", ""),
                    "summary": content,
                    "rawContent": raw_content,
                    "source": self._source_name(url),
                    "category": profile.tavily_topic or self.settings.tavily_topic or "search",
                    "url": url,
                    "score": str(result.get("score", "")),
                    "publishedDate": result.get("published_date", "") or result.get("publishedDate", ""),
                    "favicon": result.get("favicon", ""),
                    "searchProfile": profile.name,
                }
            )
        return items
