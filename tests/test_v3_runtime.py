import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


BACKEND_DIR = Path(__file__).resolve().parents[1] / "app" / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from deerflow_result_mapper import DeerFlowResultMapper
from deerflow_runtime_client import DeerFlowRuntimeClient, DeerFlowRuntimeError
from deerflow_status import DeerFlowStatusProbe
from live_report_service_v2 import LiveReportServiceV2
from settings import get_settings


class FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload
        self.headers = {"Content-Type": "application/json"}
        self.text = json.dumps(payload, ensure_ascii=False)

    def json(self):
        return self._payload


class FakeSession:
    def get(self, url, headers=None, timeout=30):
        if url.endswith("/api/health"):
            return FakeResponse(200, {"status": "ok"})
        return FakeResponse(404, {"detail": "not found"})

    def post(self, url, headers=None, json=None, timeout=30):
        if url.endswith("/api/skills/industry-report-skill/run"):
            return FakeResponse(
                200,
                {
                    "data": {
                        "report": {
                            "markdown": "# 航运融资租赁行业报告\n\n## 核心结论\nDeerFlow 接入链路验证成功。"
                        }
                    },
                    "echo": json,
                },
            )
        if url.endswith("/skills/industry-report-skill/run"):
            return FakeResponse(404, {"detail": "legacy path disabled"})
        return FakeResponse(404, {"detail": "not found"})


class DeerFlowRuntimeTests(unittest.TestCase):
    def test_client_probe_and_run_skill_with_api_fallback_endpoint(self):
        client = DeerFlowRuntimeClient(
            base_url="http://deerflow.local",
            timeout=5,
            probe_timeout=2,
            session=FakeSession(),
        )

        status = client.probe()
        result = client.run_skill("industry-report-skill", {"topic": "航运融资租赁", "timeRange": "7d"})

        self.assertTrue(status["runtimeConfigured"])
        self.assertTrue(status["runtimeReachable"])
        self.assertEqual(status["probeEndpoint"], "http://deerflow.local/api/health")
        self.assertEqual(result["_deerflow"]["candidate"], "api-skill-run")
        self.assertEqual(result["echo"]["topic"], "航运融资租赁")

    def test_result_mapper_handles_nested_markdown_payload(self):
        mapper = DeerFlowResultMapper()

        payload = {
            "data": {
                "report": {
                    "markdown": "# 行业报告\n\n## 趋势判断\n需求持续回升。"
                }
            }
        }
        mapped = mapper.to_report_payload(payload)

        self.assertEqual(mapped["mode"], "deerflow")
        self.assertIn("趋势判断", mapped["markdown"])
        self.assertIn("<h1>", mapped["html"])

    def test_service_falls_back_to_local_when_deerflow_raises(self):
        service = LiveReportServiceV2()
        local_result = {
            "mode": "local",
            "topic": "航运融资租赁",
            "timeRange": "7d",
            "itemCount": "1",
            "markdown": "# 本地报告\n\nDeerFlow 不可用时已切回本地链路。",
            "html": "<h1>本地报告</h1>",
        }

        with patch.object(service.deerflow_client, "is_configured", return_value=True):
            with patch.object(
                service.deerflow_client,
                "run_skill",
                side_effect=DeerFlowRuntimeError("mock deerflow failure"),
            ):
                with patch.object(service, "generate_with_local_chain", return_value=local_result):
                    result = service.generate("航运融资租赁", "7d", prefer_deerflow=True)

        self.assertEqual(result["mode"], "local")
        self.assertEqual(result["requestedMode"], "deerflow")
        self.assertEqual(result["fallbackReason"], "mock deerflow failure")

    def test_status_probe_reports_effective_local_when_deerflow_unreachable(self):
        probe = DeerFlowStatusProbe()

        with patch.object(probe.selector, "current_mode", return_value="deerflow"):
            with patch.object(
                probe.client,
                "probe",
                return_value={
                    "runtimeConfigured": True,
                    "runtimeReachable": False,
                    "statusCode": None,
                    "probeEndpoint": "",
                    "message": "probe failed",
                },
            ):
                status = probe.inspect()

        self.assertEqual(status["preferredMode"], "deerflow")
        self.assertEqual(status["effectiveMode"], "local")
        self.assertTrue(status["fallbackActive"])

    def test_settings_reads_skill_name_from_environment_at_instantiation_time(self):
        with patch.dict("os.environ", {"DEERFLOW_SKILL_NAME": "custom-report-skill", "PREFER_DEERFLOW": "false"}):
            settings = get_settings()

        self.assertEqual(settings.deerflow_skill_name, "custom-report-skill")
        self.assertFalse(settings.prefer_deerflow)


if __name__ == "__main__":
    unittest.main()
