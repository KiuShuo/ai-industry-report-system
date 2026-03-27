import os
from dataclasses import dataclass, field


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default)


def _env_bool(name: str, default: str = "true") -> bool:
    return os.getenv(name, default).lower() == "true"


@dataclass
class RuntimeSettings:
    tavily_api_key: str = field(default_factory=lambda: _env("TAVILY_API_KEY", ""))
    deepseek_api_key: str = field(default_factory=lambda: _env("DEEPSEEK_API_KEY", ""))
    deerflow_base_url: str = field(default_factory=lambda: _env("DEERFLOW_BASE_URL", ""))
    deerflow_api_key: str = field(default_factory=lambda: _env("DEERFLOW_API_KEY", ""))
    deerflow_skill_name: str = field(default_factory=lambda: _env("DEERFLOW_SKILL_NAME", "industry-report-skill"))
    prefer_deerflow: bool = field(default_factory=lambda: _env_bool("PREFER_DEERFLOW", "true"))


def get_settings() -> RuntimeSettings:
    return RuntimeSettings()
