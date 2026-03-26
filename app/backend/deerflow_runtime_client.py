import os
from typing import Any, Dict, Optional

import requests


class DeerFlowRuntimeClient:
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        self.base_url = (base_url or os.getenv("DEERFLOW_BASE_URL", "")).rstrip("/")
        self.api_key = api_key or os.getenv("DEERFLOW_API_KEY", "")

    def is_configured(self) -> bool:
        return bool(self.base_url)

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def run_skill(self, skill_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not self.is_configured():
            return {
                "status": "stub",
                "skill": skill_name,
                "message": "DeerFlow runtime is not configured. Set DEERFLOW_BASE_URL to enable runtime calls.",
                "payload": payload,
            }

        response = requests.post(
            f"{self.base_url}/skills/{skill_name}/run",
            headers=self._headers(),
            json=payload,
            timeout=120,
        )
        response.raise_for_status()
        return response.json()
