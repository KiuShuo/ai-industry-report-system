from typing import Any, Dict

from markdown_renderer import render_markdown_to_html


class DeerFlowResultMapper:
    def to_report_payload(self, deerflow_result: Dict[str, Any]) -> Dict[str, str]:
        markdown = self._extract_markdown(deerflow_result)
        html = self._extract_html(deerflow_result)
        if markdown and not html:
            html = render_markdown_to_html(markdown)
        return {
            "mode": "deerflow",
            "markdown": markdown,
            "html": html,
        }

    def _extract_markdown(self, deerflow_result: Any) -> str:
        if not deerflow_result:
            return ""
        if isinstance(deerflow_result, str):
            return deerflow_result.strip()

        markdown = self._find_first_string(
            deerflow_result,
            ("markdown", "md", "reportMarkdown", "report_markdown"),
        )
        if markdown:
            return markdown

        sections_markdown = self._extract_sections_markdown(deerflow_result)
        if sections_markdown:
            return sections_markdown

        return self._find_report_text(deerflow_result)

    def _extract_html(self, deerflow_result: Any) -> str:
        if not deerflow_result:
            return ""
        return self._find_first_string(deerflow_result, ("html", "reportHtml", "report_html"))

    def _find_first_string(self, node: Any, keys: tuple[str, ...]) -> str:
        if isinstance(node, dict):
            for key in keys:
                value = node.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
            for nested_key in ("result", "data", "output", "report", "artifact", "response", "payload"):
                nested_value = node.get(nested_key)
                found = self._find_first_string(nested_value, keys)
                if found:
                    return found
            for value in node.values():
                found = self._find_first_string(value, keys)
                if found:
                    return found
        if isinstance(node, list):
            for item in node:
                found = self._find_first_string(item, keys)
                if found:
                    return found
        return ""

    def _extract_sections_markdown(self, node: Any) -> str:
        if isinstance(node, dict):
            sections = node.get("sections")
            if isinstance(sections, list):
                lines = []
                for section in sections:
                    if not isinstance(section, dict):
                        continue
                    title = str(section.get("title", "")).strip()
                    content = str(section.get("content", "")).strip()
                    if title and content:
                        lines.append(f"## {title}\n{content}")
                    elif content:
                        lines.append(content)
                if lines:
                    return "\n\n".join(lines)
            for value in node.values():
                found = self._extract_sections_markdown(value)
                if found:
                    return found
        if isinstance(node, list):
            for item in node:
                found = self._extract_sections_markdown(item)
                if found:
                    return found
        return ""

    def _find_report_text(self, node: Any) -> str:
        text = self._find_first_string(node, ("content", "text", "body", "result"))
        if not text:
            return ""
        score_markers = ("#", "\n", "结论", "建议", "风险", "趋势", "report")
        return text if any(marker in text for marker in score_markers) else ""
