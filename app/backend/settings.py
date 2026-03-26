import os
from dataclasses import dataclass


@dataclass
class RuntimeSettings:
    tavily_api_key: str = os.getenv("TAVILY_API_KEY", "")
    deepseek_api_key: str = os.getenv("DEEPSEEK_API_KEY", "")
    deerflow_base_url: str = os.getenv("DEERFLOW_BASE_URL", "")
    deerflow_api_key: str = os.getenv("DEERFLOW_API_KEY", "")
    prefer_deerflow: bool = os.getenv("PREFER_DEERFLOW", "true").lower() == "true"


def get_settings() -> RuntimeSettings:
    return RuntimeSettings()
