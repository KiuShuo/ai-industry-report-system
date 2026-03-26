import os
from typing import Optional

import requests


class DeepSeekConnector:
    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.deepseek.com/chat/completions", model: str = "deepseek-chat"):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY", "")
        self.base_url = base_url
        self.model = model

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def summarize(self, prompt: str) -> str:
        if not self.is_configured():
            return "DeepSeek connector not configured. Set DEEPSEEK_API_KEY in environment variables."

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are an industry research analyst."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.3,
        }

        response = requests.post(self.base_url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        return data.get("choices", [{}])[0].get("message", {}).get("content", "")
