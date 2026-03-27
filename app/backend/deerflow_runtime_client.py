import os
from typing import Any, Dict, List, Optional, Tuple

from http_client import RequestError, create_session


class DeerFlowRuntimeError(RuntimeError):
    def __init__(self, message: str, attempts: Optional[List[Dict[str, Any]]] = None):
        super().__init__(message)
        self.attempts = attempts or []


class DeerFlowRuntimeClient:
    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: Optional[float] = None,
        probe_timeout: Optional[float] = None,
        session: Optional[Any] = None,
    ):
        self.base_url = (base_url or os.getenv("DEERFLOW_BASE_URL", "")).rstrip("/")
        self.api_key = api_key or os.getenv("DEERFLOW_API_KEY", "")
        self.timeout = timeout or float(os.getenv("DEERFLOW_TIMEOUT_SECONDS", "120"))
        self.probe_timeout = probe_timeout or float(os.getenv("DEERFLOW_PROBE_TIMEOUT_SECONDS", "5"))
        self.session = session or create_session()

    def is_configured(self) -> bool:
        return bool(self.base_url)

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _join_url(self, path: str) -> str:
        normalized = path if path.startswith("/") else f"/{path}"
        return f"{self.base_url}{normalized}"

    def _health_paths(self) -> List[str]:
        raw_value = os.getenv("DEERFLOW_HEALTH_PATHS", "/health,/api/health,/status,/api/status")
        return [item.strip() for item in raw_value.split(",") if item.strip()]

    def _run_candidates(self, skill_name: str, payload: Dict[str, Any]) -> List[Tuple[str, Dict[str, Any], str]]:
        envelope = {
            "skill": skill_name,
            "input": payload,
            "payload": payload,
        }
        return [
            (self._join_url(f"/skills/{skill_name}/run"), payload, "direct-skill-run"),
            (self._join_url(f"/api/skills/{skill_name}/run"), payload, "api-skill-run"),
            (self._join_url(f"/api/v1/skills/{skill_name}/run"), payload, "api-v1-skill-run"),
            (self._join_url("/skills/run"), envelope, "skills-run-envelope"),
            (self._join_url("/api/skills/run"), envelope, "api-skills-run-envelope"),
        ]

    def _response_payload(self, response: Any) -> Any:
        content_type = response.headers.get("Content-Type", "")
        if "application/json" in content_type:
            return response.json()
        text = response.text.strip()
        return text

    def probe(self) -> Dict[str, Any]:
        if not self.is_configured():
            return {
                "runtimeConfigured": False,
                "runtimeReachable": False,
                "statusCode": None,
                "probeEndpoint": "",
                "message": "DeerFlow runtime is not configured",
            }

        attempts: List[Dict[str, Any]] = []
        for path in self._health_paths():
            url = self._join_url(path)
            try:
                response = self.session.get(url, headers=self._headers(), timeout=self.probe_timeout)
            except RequestError as exc:
                attempts.append({"endpoint": url, "error": str(exc)})
                continue

            if response.status_code < 400 or response.status_code in {401, 403}:
                return {
                    "runtimeConfigured": True,
                    "runtimeReachable": True,
                    "statusCode": response.status_code,
                    "probeEndpoint": url,
                    "message": "DeerFlow runtime probe succeeded",
                }

            attempts.append(
                {
                    "endpoint": url,
                    "statusCode": response.status_code,
                    "body": response.text[:200],
                }
            )

        return {
            "runtimeConfigured": True,
            "runtimeReachable": False,
            "statusCode": None,
            "probeEndpoint": "",
            "message": "DeerFlow runtime is configured but health probe failed",
            "attempts": attempts,
        }

    def run_skill(self, skill_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not self.is_configured():
            return {
                "status": "stub",
                "skill": skill_name,
                "message": "DeerFlow runtime is not configured. Set DEERFLOW_BASE_URL to enable runtime calls.",
                "payload": payload,
            }

        attempts: List[Dict[str, Any]] = []
        for url, body, candidate_name in self._run_candidates(skill_name, payload):
            try:
                response = self.session.post(
                    url,
                    headers=self._headers(),
                    json=body,
                    timeout=self.timeout,
                )
            except RequestError as exc:
                attempts.append({"candidate": candidate_name, "endpoint": url, "error": str(exc)})
                continue

            parsed = self._response_payload(response)
            if response.status_code < 400:
                if isinstance(parsed, dict):
                    parsed.setdefault(
                        "_deerflow",
                        {"endpoint": url, "candidate": candidate_name, "statusCode": response.status_code},
                    )
                    return parsed
                return {
                    "result": parsed,
                    "_deerflow": {"endpoint": url, "candidate": candidate_name, "statusCode": response.status_code},
                }

            attempts.append(
                {
                    "candidate": candidate_name,
                    "endpoint": url,
                    "statusCode": response.status_code,
                    "body": parsed if isinstance(parsed, str) else str(parsed),
                }
            )
            if response.status_code in {401, 403}:
                raise DeerFlowRuntimeError(
                    f"DeerFlow runtime rejected the request with status {response.status_code}.",
                    attempts=attempts,
                )
            if response.status_code not in {400, 404, 405, 422}:
                raise DeerFlowRuntimeError(
                    f"DeerFlow runtime request failed with status {response.status_code}.",
                    attempts=attempts,
                )

        raise DeerFlowRuntimeError(
            "Unable to execute DeerFlow skill with the configured endpoint candidates.",
            attempts=attempts,
        )
