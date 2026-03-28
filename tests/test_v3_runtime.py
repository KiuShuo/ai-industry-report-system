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
from official_sources import OfficialPublicSourceConnector
from query_intent import infer_query_intent
from security_identifier import normalize_security_identifier
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


class FakeTextResponse:
    def __init__(self, status_code, text):
        self.status_code = status_code
        self.text = text
        self.headers = {"Content-Type": "text/html"}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP request failed with status {self.status_code}")


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

    def test_local_report_does_not_hallucinate_when_sources_are_empty(self):
        service = LiveReportServiceV2()

        with patch.object(service, "collect", return_value=[]):
            with patch.object(service.llm_connector, "summarize") as summarize_mock:
                result = service.generate_with_local_chain("平安银行 季报", "30d")

        summarize_mock.assert_not_called()
        self.assertEqual(result["sources"], [])
        self.assertEqual(result["searchProfile"], "earnings-and-guidance")
        self.assertIn("没有检索到可用于支撑分析结论的有效来源", result["markdown"])
        self.assertIn("本次报告未返回可用来源", result["markdown"])

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
            intent = infer_query_intent("航运融资租赁")
            profile = connector.resolve_profile("航运融资租赁", intent)
            payload = connector._build_payload("航运融资租赁", "7d", 6, profile, intent)

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

    def test_search_profile_resolution_matches_stock_industry_news(self):
        profile = resolve_search_profile("光伏行业资讯", "auto")
        self.assertEqual(profile.name, "stock-industry-news")

    def test_search_profile_resolution_matches_earnings_profile(self):
        profile = resolve_search_profile("特斯拉财报", "auto")
        self.assertEqual(profile.name, "earnings-and-guidance")

    def test_search_profile_resolution_matches_chinese_quarterly_report_profile(self):
        profile = resolve_search_profile("平安银行 季报", "auto")
        self.assertEqual(profile.name, "earnings-and-guidance")

    def test_search_profile_resolution_matches_macro_profile(self):
        profile = resolve_search_profile("美国利率与黄金走势", "auto")
        self.assertEqual(profile.name, "macro-rates-commodities")

    def test_query_intent_infers_earnings_query(self):
        intent = infer_query_intent("特斯拉 TSLA 财报")
        self.assertEqual(intent.profile_hint, "earnings-and-guidance")
        self.assertEqual(intent.ticker, "TSLA")
        self.assertEqual(intent.canonical_symbol, "US:TSLA")
        self.assertIn("earnings guidance results", intent.normalized_topic)

    def test_query_intent_infers_chinese_quarterly_report_query(self):
        intent = infer_query_intent("平安银行 季报")
        self.assertEqual(intent.profile_hint, "earnings-and-guidance")

    def test_query_intent_infers_company_news_query_from_stock_code(self):
        intent = infer_query_intent("600519 公司公告")
        self.assertEqual(intent.profile_hint, "ticker-company-news")
        self.assertEqual(intent.security_code, "600519")
        self.assertEqual(intent.canonical_symbol, "SHSE:600519")

    def test_query_intent_infers_macro_query(self):
        intent = infer_query_intent("美债收益率和黄金")
        self.assertEqual(intent.profile_hint, "macro-rates-commodities")

    def test_security_identifier_normalizes_us_symbol(self):
        identifier = normalize_security_identifier("TSLA")
        self.assertEqual(identifier.canonical_symbol, "US:TSLA")
        self.assertEqual(identifier.market, "US")

    def test_security_identifier_normalizes_cn_symbol(self):
        identifier = normalize_security_identifier("600519")
        self.assertEqual(identifier.canonical_symbol, "SHSE:600519")
        self.assertEqual(identifier.market, "CN")

    def test_security_identifier_normalizes_hk_symbol(self):
        identifier = normalize_security_identifier("0700.HK")
        self.assertEqual(identifier.canonical_symbol, "HKEX:0700")
        self.assertEqual(identifier.market, "HK")

    def test_evidence_excerpt_prefers_raw_content(self):
        service = LiveReportServiceV2()
        excerpt = service._evidence_excerpt(
            {
                "summary": "摘要文本",
                "rawContent": "原文正文内容",
            }
        )

        self.assertEqual(excerpt, "原文正文内容")

    def test_official_source_connector_parses_stats_rss(self):
        rss_text = """
        <rss>
          <channel>
            <item>
              <title>2026年3月制造业采购经理指数运行情况</title>
              <link>https://www.stats.gov.cn/example/pmi.html</link>
              <pubDate>Fri, 28 Mar 2026 10:00:00 GMT</pubDate>
              <description>3月份制造业PMI为50.8%。</description>
            </item>
          </channel>
        </rss>
        """

        def fake_request(method, url, headers=None, timeout=30, json_body=None):
            self.assertEqual(method, "GET")
            self.assertIn("stats.gov.cn", url)
            return FakeTextResponse(200, rss_text)

        with patch.dict(
            "os.environ",
            {
                "ENABLE_OFFICIAL_SOURCES": "true",
                "OFFICIAL_SOURCE_NAMES": "stats",
                "OFFICIAL_SOURCE_MAX_RESULTS": "3",
            },
        ):
            with patch("official_sources.request_json", side_effect=fake_request):
                connector = OfficialPublicSourceConnector()
                results = connector.search("制造业 PMI", "30d", 3)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["source"], "国家统计局")
        self.assertEqual(results[0]["sourceBackend"], "official")
        self.assertEqual(results[0]["sourceChannel"], "stats")
        self.assertIn("PMI", results[0]["summary"])

    def test_official_source_connector_parses_csrc_html_list(self):
        html_text = """
        <ul class="list">
          <li><a href="/csrc/c100040/c7654321/content.shtml">证监会发布上市公司信息披露监管动态</a><span>2026-03-27</span></li>
        </ul>
        """

        def fake_request(method, url, headers=None, timeout=30, json_body=None):
            self.assertEqual(method, "GET")
            self.assertIn("csrc.gov.cn", url)
            return FakeTextResponse(200, html_text)

        with patch.dict(
            "os.environ",
            {
                "ENABLE_OFFICIAL_SOURCES": "true",
                "OFFICIAL_SOURCE_NAMES": "csrc",
                "OFFICIAL_SOURCE_MAX_RESULTS": "2",
            },
        ):
            with patch("official_sources.request_json", side_effect=fake_request):
                connector = OfficialPublicSourceConnector()
                results = connector.search("证券监管", "30d", 2)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["source"], "中国证监会")
        self.assertEqual(results[0]["sourceChannel"], "csrc")
        self.assertTrue(results[0]["url"].startswith("https://www.csrc.gov.cn/"))

    def test_official_source_connector_parses_cninfo_homepage_notice(self):
        html_text = """
        <div class="headlines">
          <a href="/new/disclosure/detail?plate=szse&stockCode=000001&announcementId=123456">
            平安银行：2026年第一季度报告
          </a>
          <span>2026-03-28</span>
        </div>
        """

        def fake_request(method, url, headers=None, timeout=30, json_body=None):
            self.assertEqual(method, "GET")
            self.assertEqual(url, "https://www.cninfo.com.cn/")
            return FakeTextResponse(200, html_text)

        with patch.dict(
            "os.environ",
            {
                "ENABLE_OFFICIAL_SOURCES": "true",
                "OFFICIAL_SOURCE_NAMES": "cninfo",
                "OFFICIAL_SOURCE_MAX_RESULTS": "2",
            },
        ):
            with patch("official_sources.request_json", side_effect=fake_request):
                connector = OfficialPublicSourceConnector()
                results = connector.search("平安银行 季报", "30d", 2)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["source"], "巨潮资讯")
        self.assertEqual(results[0]["sourceChannel"], "cninfo")
        self.assertIn("季度报告", results[0]["title"])
        self.assertTrue(results[0]["url"].startswith("https://www.cninfo.com.cn/"))

    def test_collect_prioritizes_official_sources_before_tavily(self):
        service = LiveReportServiceV2()
        official_items = [
            {
                "title": "国家统计局发布工业数据",
                "summary": "官方数据摘要",
                "source": "国家统计局",
                "sourceBackend": "official",
                "url": "https://www.stats.gov.cn/example/data.html",
            }
        ]
        tavily_items = [
            {
                "title": "媒体解读工业数据",
                "summary": "媒体摘要",
                "source": "example.com",
                "url": "https://example.com/news",
            }
        ]

        with patch.object(service.official_connector, "is_enabled", return_value=True):
            with patch.object(service.official_connector, "search", return_value=official_items):
                with patch.object(service.search_connector, "is_configured", return_value=True):
                    with patch.object(service.search_connector, "search", return_value=tavily_items):
                        collected = service.collect("工业数据", "7d")

        self.assertEqual(len(collected), 2)
        self.assertEqual(collected[0]["sourceBackend"], "official")
        self.assertEqual(collected[0]["sourceId"], "S1")
        self.assertEqual(collected[1]["source"], "example.com")

    def test_settings_enable_exchange_and_cninfo_sources_by_default(self):
        settings = get_settings()

        self.assertIn("cninfo", settings.official_source_names)
        self.assertIn("sse", settings.official_source_names)
        self.assertIn("szse", settings.official_source_names)

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
