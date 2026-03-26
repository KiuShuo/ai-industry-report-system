from settings import get_settings


class RuntimeModeSelector:
    def __init__(self):
        self.settings = get_settings()

    def prefer_deerflow(self) -> bool:
        return self.settings.prefer_deerflow and bool(self.settings.deerflow_base_url)

    def current_mode(self) -> str:
        return "deerflow" if self.prefer_deerflow() else "local"
