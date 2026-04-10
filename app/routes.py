from fastapi import APIRouter, HTTPException, status

from app.models import (
    HeartbeatResponse,
    MonitorStatus,
    MonitorStatusResponse,
    PauseResponse,
    RegisterMonitorRequest,
    RegisterMonitorResponse,
)
from app.store import Monitor, monitor_store
from app.timer import cancel_timer, start_timer

router = APIRouter()


@router.post(
    "/monitors",
    status_code=status.HTTP_201_CREATED,
    response_model=RegisterMonitorResponse,
    summary="Register a new device monitor",
)
async def register_monitor(body: RegisterMonitorRequest):
    existing = monitor_store.get(body.id)
    if existing:
        cancel_timer(existing)

    monitor = Monitor(
        id=body.id,
        timeout=body.timeout,
        alert_email=body.alert_email,
        status=MonitorStatus.ACTIVE,
    )
    monitor_store[body.id] = monitor
    start_timer(monitor)

    return RegisterMonitorResponse(
        message=f"Monitor '{body.id}' registered. Countdown started for {body.timeout}s.",
        id=monitor.id,
        timeout=monitor.timeout,
        status=monitor.status,
    )


@router.post(
    "/monitors/{monitor_id}/heartbeat",
    response_model=HeartbeatResponse,
    summary="Send a heartbeat to reset the countdown",
)
async def heartbeat(monitor_id: str):
    monitor = monitor_store.get(monitor_id)
    if not monitor:
        raise HTTPException(status_code=404, detail=f"Monitor '{monitor_id}' not found.")

    if monitor.status == MonitorStatus.DOWN:
        raise HTTPException(
            status_code=404,
            detail=f"Monitor '{monitor_id}' is already down. Re-register it to start fresh.",
        )

    cancel_timer(monitor)
    monitor.status = MonitorStatus.ACTIVE
    start_timer(monitor)

    return HeartbeatResponse(
        message=f"Heartbeat received. Timer reset to {monitor.timeout}s.",
        id=monitor.id,
        status=monitor.status,
    )


@router.post(
    "/monitors/{monitor_id}/pause",
    response_model=PauseResponse,
    summary="Pause monitoring to suppress false alerts during maintenance",
)
async def pause_monitor(monitor_id: str):
    monitor = monitor_store.get(monitor_id)
    if not monitor:
        raise HTTPException(status_code=404, detail=f"Monitor '{monitor_id}' not found.")

    if monitor.status == MonitorStatus.DOWN:
        raise HTTPException(
            status_code=409,
            detail=f"Monitor '{monitor_id}' is already down. Re-register to reset.",
        )

    if monitor.status == MonitorStatus.PAUSED:
        return PauseResponse(
            message=f"Monitor '{monitor_id}' is already paused.",
            id=monitor.id,
            status=monitor.status,
        )

    cancel_timer(monitor)
    monitor.status = MonitorStatus.PAUSED

    return PauseResponse(
        message=f"Monitor '{monitor_id}' paused. No alerts will fire until a heartbeat is received.",
        id=monitor.id,
        status=monitor.status,
    )


@router.get(
    "/monitors/{monitor_id}",
    response_model=MonitorStatusResponse,
    summary="Inspect the current state of a monitor",
)
async def get_monitor(monitor_id: str):
    monitor = monitor_store.get(monitor_id)
    if not monitor:
        raise HTTPException(status_code=404, detail=f"Monitor '{monitor_id}' not found.")

    return MonitorStatusResponse(
        id=monitor.id,
        status=monitor.status,
        timeout=monitor.timeout,
        alert_email=monitor.alert_email,
        time_remaining=monitor.time_remaining(),
    )