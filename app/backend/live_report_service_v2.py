from typing import Dict, List

from tavily_connector import TavilyConnector
from deepseek_connector import DeepSeekConnector
from analysis_pipeline import AnalysisPipeline
from markdown_renderer import render_markdown_to_html
from deerflow_runtime_client import DeerFlowRuntimeClient, DeerFlowRuntimeError
from deerflow_result_mapper import DeerFlowResultMapper
from settings import get_settings


class LiveReportServiceV2:
    def __init__(self):
        self.search_connector = TavilyConnector()
        self.llm_connector = DeepSeekConnector()
        self.pipeline = AnalysisPipeline()
        self.deerflow_client = DeerFlowRuntimeClient()
        self.result_mapper = DeerFlowResultMapper()
        self.settings = get_settings()

    def collect(self, topic: str, time_range: str) -> List[Dict[str, str]]:
        return self.search_connector.search(topic, time_range)

    def analyze(self, items: List[Dict[str, str]]) -> List[Dict[str, str]]:
        return self.pipeline.run(items)

    def build_prompt(self, topic: str, time_range: str, analyzed_items: List[Dict[str, str]]) -> str:
        lines = [
            "请基于以下行业动态生成结构化行业分析报告。",
            f"主题：{topic}",
            f"时间范围：{time_range}",
            "输出要求：包含核心结论、重点动态、趋势判断、风险提示、行动建议。",
            "以下是动态列表：",
        ]
        for index, item in enumerate(analyzed_items, start=1):
            lines.append(
                f"{index}. 标题：{item.get('title', '')}；分类：{item.get('category', '')}；摘要：{item.get('summary', '')}"
            )
        return "\n".join(lines)

    def generate_with_local_chain(self, topic: str, time_range: str) -> Dict[str, str]:
        raw_items = self.collect(topic, time_range)
        analyzed_items = self.analyze(raw_items)
        prompt = self.build_prompt(topic, time_range, analyzed_items)
        markdown = self.llm_connector.summarize(prompt)
        html = render_markdown_to_html(markdown) if markdown else ""
        return {
            "mode": "local",
            "topic": topic,
            "timeRange": time_range,
            "itemCount": str(len(analyzed_items)),
            "markdown": markdown,
            "html": html,
        }

    def generate_with_deerflow(self, topic: str, time_range: str) -> Dict[str, str]:
        payload = {"topic": topic, "timeRange": time_range}
        skill_name = self.settings.deerflow_skill_name
        result = self.deerflow_client.run_skill(skill_name, payload)
        return {
            "mode": "deerflow",
            "requestedMode": "deerflow",
            "skillName": skill_name,
            "topic": topic,
            "timeRange": time_range,
            "result": result,
            "deerflow": result.get("_deerflow", {}),
        }

    def generate(self, topic: str, time_range: str, prefer_deerflow: bool = True) -> Dict[str, str]:
        if prefer_deerflow and self.deerflow_client.is_configured():
            try:
                deerflow_result = self.generate_with_deerflow(topic, time_range)
                mapped_preview = self.result_mapper.to_report_payload(deerflow_result.get("result", {}))
                if mapped_preview.get("markdown") or mapped_preview.get("html"):
                    return deerflow_result
                fallback = self.generate_with_local_chain(topic, time_range)
                fallback["requestedMode"] = "deerflow"
                fallback["fallbackReason"] = "DeerFlow response did not include a usable report artifact."
                fallback["deerflow"] = deerflow_result.get("deerflow", {})
                return fallback
            except DeerFlowRuntimeError as exc:
                fallback = self.generate_with_local_chain(topic, time_range)
                fallback["requestedMode"] = "deerflow"
                fallback["fallbackReason"] = str(exc)
                if exc.attempts:
                    fallback["deerflowAttempts"] = exc.attempts
                return fallback

        local_result = self.generate_with_local_chain(topic, time_range)
        local_result["requestedMode"] = "local"
        return local_result
