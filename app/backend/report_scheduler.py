import threading
import time
from datetime import datetime
from typing import Callable


class SimpleReportScheduler:
    def __init__(self, interval_seconds: int, task_func: Callable):
        self.interval = interval_seconds
        self.task_func = task_func
        self._running = False
        self._thread = None

    def _loop(self):
        while self._running:
            try:
                print(f"[Scheduler] trigger at {datetime.now()}")
                self.task_func()
            except Exception as e:
                print(f"[Scheduler] error: {e}")
            time.sleep(self.interval)

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
