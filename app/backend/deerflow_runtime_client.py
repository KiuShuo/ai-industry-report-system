import os
import time
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
        self.poll_interval = float(os.getenv("DEERFLOW_POLL_INTERVAL_SECONDS", "2"))
        self.poll_max_attempts = int(os.getenv("DEERFLOW_POLL_MAX_ATTEMPTS", "30"))
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
            try:
                return response.json()
            except Exception:
                return response.text.strip()
        text = response.text.strip()
        return text

    def _run_status_paths(self, token: str, skill_name: str) -> List[str]:
        return [
            f"/runs/{token}",
            f"/api/runs/{token}",
            f"/api/v1/runs/{token}",
            f"/jobs/{token}",
            f"/api/jobs/{token}",
            f"/tasks/{token}",
            f"/api/tasks/{token}",
            f"/skills/{skill_name}/runs/{token}",
            f"/api/skills/{skill_name}/runs/{token}",
        ]

    def _normalize_status_endpoint(self, endpoint: str) -> str:
        if endpoint.startswith("http://") or endpoint.startswith("https://"):
            return endpoint
        return self._join_url(endpoint)

    def _dedupe_urls(self, items: List[str]) -> List[str]:
        seen = set()
        deduped: List[str] = []
        for item in items:
            if not item or item in seen:
                continue
            seen.add(item)
            deduped.append(item)
        return deduped

    def _find_first_value(self, node: Any, keys: Tuple[str, ...]) -> Any:
        if isinstance(node, dict):
            for key in keys:
                value = node.get(key)
                if value not in (None, "", [], {}):
                    return value
            for nested_key in ("data", "result", "output", "run", "job", "task", "meta", "payload", "response"):
                nested_value = node.get(nested_key)
                found = self._find_first_value(nested_value, keys)
                if found not in (None, "", [], {}):
                    return found
            for value in node.values():
                found = self._find_first_value(value, keys)
                if found not in (None, "", [], {}):
                    return found
        if isinstance(node, list):
            for item in node:
                found = self._find_first_value(item, keys)
                if found not in (None, "", [], {}):
                    return found
        return None

    def _extract_status(self, payload: Any) -> str:
        value = self._find_first_value(payload, ("status", "state", "phase"))
        return str(value).strip().lower() if value is not None else ""

    def _extract_async_reference(self, response: Any, payload: Any) -> Dict[str, str]:
        location = response.headers.get("Location", "") or response.headers.get("location", "")
        endpoint = self._normalize_status_endpoint(location) if location else ""
        token = self._find_first_value(
            payload,
            ("runId", "run_id", "jobId", "job_id", "taskId", "task_id", "executionId", "execution_id", "id"),
        )

        normalized_token = str(token).strip() if token is not None else ""
        if endpoint or normalized_token:
            return {
                "statusEndpoint": endpoint,
                "token": normalized_token,
                "status": self._extract_status(payload),
            }
        return {}

    def _status_candidates(self, skill_name: str, async_reference: Dict[str, str]) -> List[str]:
        candidates: List[str] = []
        if async_reference.get("statusEndpoint"):
            candidates.append(async_reference["statusEndpoint"])
        token = async_reference.get("token", "")
        if token:
            candidates.extend(self._join_url(path) for path in self._run_status_paths(token, skill_name))
        return self._dedupe_urls(candidates)

    def _pending_statuses(self) -> set[str]:
        return {"accepted", "pending", "queued", "running", "processing", "in_progress", "created"}

    def _failure_statuses(self) -> set[str]:
        return {"failed", "error", "cancelled", "canceled", "timeout", "expired"}

    def _finalize_payload(
        self,
        payload: Any,
        *,
        endpoint: str,
        candidate_name: str,
        status_code: int,
        async_reference: Optional[Dict[str, str]] = None,
        poll_attempts: int = 0,
    ) -> Dict[str, Any]:
        metadata: Dict[str, Any] = {
            "endpoint": endpoint,
            "candidate": candidate_name,
            "statusCode": status_code,
        }
        if async_reference:
            metadata["async"] = async_reference
        if poll_attempts:
            metadata["pollAttempts"] = poll_attempts

        if isinstance(payload, dict):
            payload.setdefault("_deerflow", metadata)
            return payload
        return {"result": payload, "_deerflow": metadata}

    def _poll_run_result(
        self,
        *,
        skill_name: str,
        candidate_name: str,
        async_reference: Dict[str, str],
        attempts: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        status_urls = self._status_candidates(skill_name, async_reference)
        if not status_urls:
            raise DeerFlowRuntimeError(
                "DeerFlow runtime accepted the task but did not provide a pollable run identifier.",
                attempts=attempts,
            )

        for poll_attempt in range(1, self.poll_max_attempts + 1):
            for url in status_urls:
                try:
                    response = self.session.get(url, headers=self._headers(), timeout=self.timeout)
                except RequestError as exc:
                    attempts.append(
                        {
                            "candidate": candidate_name,
                            "endpoint": url,
                            "phase": "poll",
                            "pollAttempt": poll_attempt,
                            "error": str(exc),
                        }
                    )
                    continue

                parsed = self._response_payload(response)
                if response.status_code >= 400:
                    attempts.append(
                        {
                            "candidate": candidate_name,
                            "endpoint": url,
                            "phase": "poll",
                            "pollAttempt": poll_attempt,
                            "statusCode": response.status_code,
                            "body": parsed if isinstance(parsed, str) else str(parsed),
                        }
                    )
                    continue

                if not parsed:
                    continue

                status = self._extract_status(parsed)
                if status in self._failure_statuses():
                    raise DeerFlowRuntimeError(
                        f"DeerFlow run failed with status '{status}'.",
                        attempts=attempts,
                    )
                if status in self._pending_statuses():
                    continue

                return self._finalize_payload(
                    parsed,
                    endpoint=url,
                    candidate_name=candidate_name,
                    status_code=response.status_code,
                    async_reference=async_reference,
                    poll_attempts=poll_attempt,
                )

            if poll_attempt < self.poll_max_attempts:
                time.sleep(self.poll_interval)

        raise DeerFlowRuntimeError(
            "DeerFlow runtime did not finish before polling timed out.",
            attempts=attempts,
        )

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
                async_reference = self._extract_async_reference(response, parsed)
                status = self._extract_status(parsed)
                should_poll = bool(async_reference) and (
                    response.status_code == 202 or status in self._pending_statuses()
                )
                if should_poll:
                    return self._poll_run_result(
                        skill_name=skill_name,
                        candidate_name=candidate_name,
                        async_reference=async_reference,
                        attempts=attempts,
                    )
                return self._finalize_payload(
                    parsed,
                    endpoint=url,
                    candidate_name=candidate_name,
                    status_code=response.status_code,
                )

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
