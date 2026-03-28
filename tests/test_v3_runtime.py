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
from search_profiles import resolve_search_profile
from settings import get_settings
from tavily_connector import TavilyConnector


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


class AsyncFakeSession:
    def __init__(self):
        self.poll_count = 0

    def get(self, url, headers=None, timeout=30):
        if url.endswith("/api/runs/run-123"):
            self.poll_count += 1
            if self.poll_count == 1:
                return FakeResponse(200, {"status": "running", "runId": "run-123"})
            return FakeResponse(
                200,
                {
                    "status": "completed",
                    "result": {
                        "report": {
                            "markdown": "# 异步行业报告\n\n## 核心结论\n轮询链路验证成功。"
                        }
                    },
                },
            )
        return FakeResponse(404, {"detail": "not found"})

    def post(self, url, headers=None, json=None, timeout=30):
        if url.endswith("/api/skills/industry-report-skill/run"):
            return FakeResponse(202, {"status": "queued", "runId": "run-123"})
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

    def test_result_mapper_prefers_report_artifacts_when_available(self):
        mapper = DeerFlowResultMapper()

        payload = {
            "artifacts": [
                {"name": "report.md", "content": "# Artifact Report\n\n## 核心结论\n产物抽取成功。"},
                {"name": "report.html", "content": "<h1>Artifact Report</h1>"},
            ]
        }
        mapped = mapper.to_report_payload(payload)

        self.assertIn("Artifact Report", mapped["markdown"])
        self.assertIn("<h1>Artifact Report</h1>", mapped["html"])

    def test_client_polls_async_run_until_completion(self):
        client = DeerFlowRuntimeClient(
            base_url="http://deerflow.local",
            timeout=5,
            probe_timeout=2,
            session=AsyncFakeSession(),
        )
        client.poll_interval = 0
        client.poll_max_attempts = 3

        result = client.run_skill("industry-report-skill", {"topic": "航运融资租赁", "timeRange": "7d"})

        self.assertEqual(result["_deerflow"]["async"]["token"], "run-123")
        self.assertEqual(result["_deerflow"]["pollAttempts"], 2)
        self.assertIn("异步行业报告", result["result"]["report"]["markdown"])

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

    def test_analysis_pipeline_preserves_source_metadata(self):
        service = LiveReportServiceV2()

        analyzed = service.analyze(
            [
                {
                    "sourceId": "S1",
                    "title": "示例来源",
                    "summary": "来源摘要",
                    "category": "search",
                    "source": "example.com",
                    "url": "https://example.com/report",
                }
            ]
        )

        self.assertEqual(analyzed[0]["sourceId"], "S1")
        self.assertEqual(analyzed[0]["source"], "example.com")
        self.assertEqual(analyzed[0]["url"], "https://example.com/report")

    def test_local_report_appends_sources_section(self):
        service = LiveReportServiceV2()
        sample_items = [
            {
                "sourceId": "S1",
                "title": "航运租赁市场更新",
                "summary": "市场规模增长。",
                "category": "search",
                "source": "example.com",
                "url": "https://example.com/report",
            }
        ]

        with patch.object(service, "collect", return_value=sample_items):
            with patch.object(service.llm_connector, "summarize", return_value="# 报告\n\n核心内容 [S1]"):
                result = service.generate_with_local_chain("航运融资租赁", "7d")

        self.assertIn("## 数据来源", result["markdown"])
        self.assertIn("[S1] 航运租赁市场更新", result["markdown"])
        self.assertIn("https://example.com/report", result["markdown"])
        self.assertEqual(result["sources"][0]["sourceId"], "S1")

    def test_tavily_connector_builds_payload_with_filters(self):
        with patch.dict(
            "os.environ",
            {
                "SEARCH_PROFILE": "auto",
                "TAVILY_TOPIC": "news",
                "TAVILY_SEARCH_DEPTH": "advanced",
                "TAVILY_INCLUDE_RAW_CONTENT": "markdown",
                "TAVILY_INCLUDE_FAVICON": "true",
                "TAVILY_INCLUDE_DOMAINS": "",
                "TAVILY_EXCLUDE_DOMAINS": "example.com",
                "TAVILY_AUTO_PARAMETERS": "false",
                "TAVILY_CHUNKS_PER_SOURCE": "4",
            },
        ):
            connector = TavilyConnector(api_key="test-key")
            profile = connector.resolve_profile("航运融资租赁")
            payload = connector._build_payload("航运融资租赁", "7d", 6, profile)

        self.assertEqual(profile.name, "shipping-finance-leasing")
        self.assertEqual(payload["topic"], "news")
        self.assertEqual(payload["search_depth"], "advanced")
        self.assertEqual(payload["include_raw_content"], "markdown")
        self.assertIn("seatrade-maritime.com", payload["include_domains"])
        self.assertIn("baike.baidu.com", payload["exclude_domains"])
        self.assertIn("example.com", payload["exclude_domains"])
        self.assertEqual(payload["chunks_per_source"], 4)
        self.assertEqual(payload["max_results"], 6)
        self.assertIn("start_date", payload)
        self.assertIn("end_date", payload)

    def test_search_profile_resolution_falls_back_to_generic(self):
        profile = resolve_search_profile("半导体设备", "auto")
        self.assertEqual(profile.name, "generic-industry")

    def test_search_profile_can_be_forced_by_env_name(self):
        profile = resolve_search_profile("任意主题", "shipping-finance-leasing")
        self.assertEqual(profile.name, "shipping-finance-leasing")

    def test_evidence_excerpt_prefers_raw_content(self):
        service = LiveReportServiceV2()
        excerpt = service._evidence_excerpt(
            {
                "summary": "摘要文本",
                "rawContent": "原文正文内容",
            }
        )

        self.assertEqual(excerpt, "原文正文内容")

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
