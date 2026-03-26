from typing import Dict, List

from tavily_connector import TavilyConnector
from deepseek_connector import DeepSeekConnector
from analysis_pipeline import AnalysisPipeline
from markdown_renderer import render_markdown_to_html
from deerflow_runtime_client import DeerFlowRuntimeClient


class LiveReportServiceV2:
    def __init__(self):
        self.search_connector = TavilyConnector()
        self.llm_connector = DeepSeekConnector()
        self.pipeline = AnalysisPipeline()
        self.deerflow_client = DeerFlowRuntimeClient()

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
        result = self.deerflow_client.run_skill("industry-report-skill", payload)
        return {
            "mode": "deerflow",
            "topic": topic,
            "timeRange": time_range,
            "result": result,
        }

    def generate(self, topic: str, time_range: str, prefer_deerflow: bool = True) -> Dict[str, str]:
        if prefer_deerflow and self.deerflow_client.is_configured():
            return self.generate_with_deerflow(topic, time_range)
        return self.generate_with_local_chain(topic, time_range)
