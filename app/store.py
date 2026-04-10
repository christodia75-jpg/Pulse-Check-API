import asyncio
import time
from dataclasses import dataclass, field
from typing import Optional

from app.models import MonitorStatus


@dataclass
class Monitor:
    id: str
    timeout: int
    alert_email: str
    status: MonitorStatus = MonitorStatus.ACTIVE
    task: Optional[asyncio.Task] = field(default=None, repr=False)
    started_at: float = field(default_factory=time.monotonic)

    def time_remaining(self) -> Optional[float]:
        """Return approximate seconds left on the countdown, or None if not running."""
        if self.status != MonitorStatus.ACTIVE or self.task is None or self.task.done():
            return None
        elapsed = time.monotonic() - self.started_at
        remaining = self.timeout - elapsed
        return max(0.0, remaining)


# Single shared in-memory store: device_id → Monitor
monitor_store: dict[str, Monitor] = {}