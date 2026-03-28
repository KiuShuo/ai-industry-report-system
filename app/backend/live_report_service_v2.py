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
        raw_items = self.search_connector.search(topic, time_range)
        collected: List[Dict[str, str]] = []
        for index, item in enumerate(raw_items, start=1):
            normalized = dict(item)
            normalized.setdefault("sourceId", f"S{index}")
            collected.append(normalized)
        return collected

    def analyze(self, items: List[Dict[str, str]]) -> List[Dict[str, str]]:
        return self.pipeline.run(items)

    def _evidence_excerpt(self, item: Dict[str, str], max_length: int = 1200) -> str:
        raw_content = (item.get("rawContent") or "").strip()
        summary = (item.get("summary") or "").strip()
        text = raw_content or summary
        if len(text) <= max_length:
            return text
        return f"{text[:max_length].rstrip()}..."

    def build_prompt(self, topic: str, time_range: str, analyzed_items: List[Dict[str, str]]) -> str:
        lines = [
            "请基于以下行业动态生成结构化行业分析报告。",
            f"主题：{topic}",
            f"时间范围：{time_range}",
            "输出要求：包含核心结论、重点动态、趋势判断、风险提示、行动建议。",
            "引用要求：在引用具体事实、数字或事件时，尽量在句末标注对应来源编号，例如 [S1]、[S2]。",
            "可信度要求：如果来源无法直接支持某个结论，请明确说明信息有限，不要编造未提供的数据。",
            "以下是动态列表：",
        ]
        for index, item in enumerate(analyzed_items, start=1):
            source_id = item.get("sourceId", f"S{index}")
            source_name = item.get("source", "") or "未知来源"
            source_url = item.get("url", "") or "无链接"
            published_date = item.get("publishedDate", "") or "未知日期"
            evidence_excerpt = self._evidence_excerpt(item)
            lines.append(
                f"{index}. 来源编号：{source_id}；标题：{item.get('title', '')}；分类：{item.get('category', '')}；发布日期：{published_date}；摘要：{item.get('summary', '')}；证据摘录：{evidence_excerpt}；来源：{source_name}；链接：{source_url}"
            )
        return "\n".join(lines)

    def build_sources_section(self, analyzed_items: List[Dict[str, str]]) -> str:
        lines = ["## 数据来源", ""]
        if not analyzed_items:
            lines.append("- 本次报告未返回可用来源。")
            return "\n".join(lines)

        seen = set()
        for item in analyzed_items:
            source_id = item.get("sourceId", "").strip() or "S?"
            title = item.get("title", "").strip() or "未命名来源"
            source_name = item.get("source", "").strip() or "未知来源"
            url = item.get("url", "").strip()
            published_date = item.get("publishedDate", "").strip()
            dedupe_key = (source_id, title, url)
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            if url:
                if published_date:
                    lines.append(f"- [{source_id}] {title} | 来源：{source_name} | 日期：{published_date} | 链接：{url}")
                else:
                    lines.append(f"- [{source_id}] {title} | 来源：{source_name} | 链接：{url}")
            else:
                if published_date:
                    lines.append(f"- [{source_id}] {title} | 来源：{source_name} | 日期：{published_date}")
                else:
                    lines.append(f"- [{source_id}] {title} | 来源：{source_name}")
        return "\n".join(lines)

    def append_sources_to_markdown(self, markdown: str, analyzed_items: List[Dict[str, str]]) -> str:
        sources_section = self.build_sources_section(analyzed_items)
        if not markdown:
            return sources_section
        if "## 数据来源" in markdown:
            return markdown
        return f"{markdown.rstrip()}\n\n---\n\n{sources_section}\n"

    def generate_with_local_chain(self, topic: str, time_range: str) -> Dict[str, str]:
        raw_items = self.collect(topic, time_range)
        analyzed_items = self.analyze(raw_items)
        search_profile = analyzed_items[0].get("searchProfile", "generic-industry") if analyzed_items else "generic-industry"
        prompt = self.build_prompt(topic, time_range, analyzed_items)
        markdown = self.llm_connector.summarize(prompt)
        markdown = self.append_sources_to_markdown(markdown, analyzed_items)
        html = render_markdown_to_html(markdown) if markdown else ""
        return {
            "mode": "local",
            "topic": topic,
            "timeRange": time_range,
            "itemCount": str(len(analyzed_items)),
            "markdown": markdown,
            "html": html,
            "sources": analyzed_items,
            "searchProfile": search_profile,
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
