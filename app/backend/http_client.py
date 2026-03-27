import json
from typing import Any, Dict, Optional
from urllib import error, request

try:
    import requests as requests_lib
except ImportError:  # pragma: no cover - exercised in environments without requests installed
    requests_lib = None


class RequestError(RuntimeError):
    pass


class SimpleResponse:
    def __init__(self, status_code: int, text: str, headers: Optional[Dict[str, str]] = None):
        self.status_code = status_code
        self.text = text
        self.headers = headers or {}

    def json(self) -> Any:
        return json.loads(self.text or "{}")

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RequestError(f"HTTP request failed with status {self.status_code}.")


class SessionAdapter:
    def __init__(self, session: Any = None):
        self.session = session

    def get(self, url: str, headers: Optional[Dict[str, str]] = None, timeout: float = 30):
        if self.session is not None:
            try:
                return self.session.get(url, headers=headers, timeout=timeout)
            except requests_lib.RequestException as exc:
                raise RequestError(str(exc)) from exc
        return request_json("GET", url, headers=headers, timeout=timeout)

    def post(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        json: Optional[Dict[str, Any]] = None,
        timeout: float = 30,
    ):
        if self.session is not None:
            try:
                return self.session.post(url, headers=headers, json=json, timeout=timeout)
            except requests_lib.RequestException as exc:
                raise RequestError(str(exc)) from exc
        return request_json("POST", url, headers=headers, json_body=json, timeout=timeout)


def create_session():
    if requests_lib is not None:
        return SessionAdapter(requests_lib.Session())
    return SessionAdapter()


def request_json(
    method: str,
    url: str,
    headers: Optional[Dict[str, str]] = None,
    json_body: Optional[Dict[str, Any]] = None,
    timeout: float = 30,
):
    if requests_lib is not None:
        try:
            return requests_lib.request(method, url, headers=headers, json=json_body, timeout=timeout)
        except requests_lib.RequestException as exc:
            raise RequestError(str(exc)) from exc

    prepared_headers = dict(headers or {})
    data = None
    if json_body is not None:
        prepared_headers.setdefault("Content-Type", "application/json")
        data = json.dumps(json_body).encode("utf-8")

    req = request.Request(url, data=data, headers=prepared_headers, method=method)
    try:
        with request.urlopen(req, timeout=timeout) as response:
            body = response.read().decode("utf-8")
            return SimpleResponse(response.status, body, dict(response.headers))
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return SimpleResponse(exc.code, body, dict(exc.headers))
    except error.URLError as exc:
        raise RequestError(str(exc)) from exc
