from datetime import datetime
from typing import Dict, List


def build_sections(topic: str, time_range: str) -> List[Dict[str, str]]:
    return [
        {"title": "报告概览", "content": f"主题：{topic}；时间范围：{time_range}；生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"},
        {"title": "核心结论", "content": f"当前 {topic} 相关动态持续活跃，建议纳入持续监控。"},
        {"title": "趋势判断", "content": "系统当前已具备任务创建、报告生成与结果查询闭环。"},
        {"title": "建议动作", "content": "后续接入真实搜索、RSS 与 DeerFlow 分析编排。"},
    ]


def render_markdown(topic: str, time_range: str) -> str:
    sections = build_sections(topic, time_range)
    lines = [f"# {topic}行业动态分析报告", ""]
    for index, section in enumerate(sections, start=1):
        lines.append(f"## {index}. {section['title']}")
        lines.append(section["content"])
        lines.append("")
    return "\n".join(lines)
