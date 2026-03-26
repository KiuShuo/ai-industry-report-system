from typing import Dict, List

from report_engine import render_markdown
from datasource_connector import MockIndustryDataSource


class ReportOrchestrator:
    def __init__(self):
        self.datasource = MockIndustryDataSource()

    def collect(self, topic: str, time_range: str) -> List[Dict[str, str]]:
        return self.datasource.search(topic, time_range)

    def build_report(self, topic: str, time_range: str) -> Dict[str, str]:
        items = self.collect(topic, time_range)
        markdown = render_markdown(topic, time_range)
        return {
            "topic": topic,
            "timeRange": time_range,
            "itemCount": str(len(items)),
            "markdown": markdown,
        }
