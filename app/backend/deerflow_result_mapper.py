from typing import Any, Dict
import json


class DeerFlowResultMapper:
    def to_report_payload(self, deerflow_result: Dict[str, Any]) -> Dict[str, str]:
        markdown = self._extract_markdown(deerflow_result)
        return {
            "mode": "deerflow",
            "markdown": markdown,
            "html": "",
        }

    def _extract_markdown(self, deerflow_result: Dict[str, Any]) -> str:
        if not deerflow_result:
            return ""
        if isinstance(deerflow_result.get("markdown"), str):
            return deerflow_result["markdown"]
        if isinstance(deerflow_result.get("result"), str):
            return deerflow_result["result"]
        return json.dumps(deerflow_result, ensure_ascii=False, indent=2)
