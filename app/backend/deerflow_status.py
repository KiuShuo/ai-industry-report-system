from typing import Dict

from deerflow_runtime_client import DeerFlowRuntimeClient
from runtime_mode_selector import RuntimeModeSelector


class DeerFlowStatusProbe:
    def __init__(self):
        self.client = DeerFlowRuntimeClient()
        self.selector = RuntimeModeSelector()

    def inspect(self) -> Dict[str, object]:
        configured = self.client.is_configured()
        return {
            "runtimeConfigured": configured,
            "preferredMode": self.selector.current_mode(),
            "deerflowBaseUrlPresent": configured,
            "message": "DeerFlow runtime is configured" if configured else "DeerFlow runtime is not configured",
        }
