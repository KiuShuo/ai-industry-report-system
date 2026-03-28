import os
from dataclasses import dataclass, field
from typing import List


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default)


def _env_bool(name: str, default: str = "true") -> bool:
    return os.getenv(name, default).lower() == "true"


def _env_csv(name: str, default: str = "") -> List[str]:
    raw_value = os.getenv(name, default)
    if not raw_value:
        return []
    return [item.strip() for item in raw_value.split(",") if item.strip()]


@dataclass
class RuntimeSettings:
    tavily_api_key: str = field(default_factory=lambda: _env("TAVILY_API_KEY", ""))
    search_profile: str = field(default_factory=lambda: _env("SEARCH_PROFILE", "auto"))
    enable_official_sources: bool = field(default_factory=lambda: _env_bool("ENABLE_OFFICIAL_SOURCES", "true"))
    official_source_names: List[str] = field(default_factory=lambda: _env_csv("OFFICIAL_SOURCE_NAMES", "cninfo,stats,csrc,sse,szse,miit,safe,customs"))
    official_source_max_results: int = field(default_factory=lambda: int(_env("OFFICIAL_SOURCE_MAX_RESULTS", "2")))
    official_source_timeout: float = field(default_factory=lambda: float(_env("OFFICIAL_SOURCE_TIMEOUT", "12")))
    tavily_topic: str = field(default_factory=lambda: _env("TAVILY_TOPIC", "news"))
    tavily_search_depth: str = field(default_factory=lambda: _env("TAVILY_SEARCH_DEPTH", "advanced"))
    tavily_include_answer: bool = field(default_factory=lambda: _env_bool("TAVILY_INCLUDE_ANSWER", "false"))
    tavily_include_raw_content: str = field(default_factory=lambda: _env("TAVILY_INCLUDE_RAW_CONTENT", "markdown"))
    tavily_include_favicon: bool = field(default_factory=lambda: _env_bool("TAVILY_INCLUDE_FAVICON", "true"))
    tavily_include_domains: List[str] = field(default_factory=lambda: _env_csv("TAVILY_INCLUDE_DOMAINS", ""))
    tavily_exclude_domains: List[str] = field(default_factory=lambda: _env_csv("TAVILY_EXCLUDE_DOMAINS", "baike.baidu.com,linkedin.com"))
    tavily_country: str = field(default_factory=lambda: _env("TAVILY_COUNTRY", ""))
    tavily_auto_parameters: bool = field(default_factory=lambda: _env_bool("TAVILY_AUTO_PARAMETERS", "false"))
    tavily_chunks_per_source: int = field(default_factory=lambda: int(_env("TAVILY_CHUNKS_PER_SOURCE", "3")))
    deepseek_api_key: str = field(default_factory=lambda: _env("DEEPSEEK_API_KEY", ""))
    deerflow_base_url: str = field(default_factory=lambda: _env("DEERFLOW_BASE_URL", ""))
    deerflow_api_key: str = field(default_factory=lambda: _env("DEERFLOW_API_KEY", ""))
    deerflow_skill_name: str = field(default_factory=lambda: _env("DEERFLOW_SKILL_NAME", "industry-report-skill"))
    prefer_deerflow: bool = field(default_factory=lambda: _env_bool("PREFER_DEERFLOW", "true"))


def get_settings() -> RuntimeSettings:
    return RuntimeSettings()
