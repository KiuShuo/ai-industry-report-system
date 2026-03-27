from typing import Dict

from deerflow_runtime_client import DeerFlowRuntimeClient
from runtime_mode_selector import RuntimeModeSelector


class DeerFlowStatusProbe:
    def __init__(self):
        self.client = DeerFlowRuntimeClient()
        self.selector = RuntimeModeSelector()

    def inspect(self) -> Dict[str, object]:
        status = self.client.probe()
        preferred_mode = self.selector.current_mode()
        runtime_reachable = bool(status.get("runtimeReachable"))
        status["preferredMode"] = preferred_mode
        status["effectiveMode"] = "deerflow" if preferred_mode == "deerflow" and runtime_reachable else "local"
        status["fallbackActive"] = preferred_mode == "deerflow" and not runtime_reachable
        status["deerflowBaseUrlPresent"] = status.get("runtimeConfigured", False)
        return status
