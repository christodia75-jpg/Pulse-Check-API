import asyncio
import logging
from datetime import datetime, timezone

from app.models import MonitorStatus
from app.store import Monitor, monitor_store

logger = logging.getLogger("pulse-check")


def _fire_alert(monitor: Monitor) -> None:
    """Log a critical alert. In production this would dispatch to a webhook / email."""
    alert_payload = {
        "ALERT": f"Device {monitor.id} is down!",
        "time": datetime.now(timezone.utc).isoformat(),
        "alert_email": monitor.alert_email,
    }
    logger.critical(alert_payload)


async def _countdown(monitor: Monitor) -> None:
    """
    Coroutine that sleeps for `timeout` seconds.
    If it completes without being cancelled → the device is down → fire alert.
    If cancelled → heartbeat or pause arrived in time → no alert.
    """
    try:
        await asyncio.sleep(monitor.timeout)
    except asyncio.CancelledError:
        return

    if monitor_store.get(monitor.id) is monitor:
        monitor.status = MonitorStatus.DOWN
        _fire_alert(monitor)


def start_timer(monitor: Monitor) -> asyncio.Task:
    """Kick off (or restart) the countdown task for a monitor."""
    import time
    monitor.started_at = time.monotonic()
    task = asyncio.create_task(_countdown(monitor), name=f"timer-{monitor.id}")
    monitor.task = task
    return task


def cancel_timer(monitor: Monitor) -> None:
    """Cancel the running countdown task without triggering an alert."""
    if monitor.task and not monitor.task.done():
        monitor.task.cancel()