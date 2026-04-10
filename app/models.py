from enum import Enum
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class MonitorStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    DOWN = "down"


class RegisterMonitorRequest(BaseModel):
    id: str = Field(..., examples=["device-123"])
    timeout: int = Field(..., gt=0, description="Countdown duration in seconds", examples=[60])
    alert_email: EmailStr = Field(..., examples=["admin@critmon.com"])


class RegisterMonitorResponse(BaseModel):
    message: str
    id: str
    timeout: int
    status: MonitorStatus


class HeartbeatResponse(BaseModel):
    message: str
    id: str
    status: MonitorStatus


class PauseResponse(BaseModel):
    message: str
    id: str
    status: MonitorStatus


class MonitorStatusResponse(BaseModel):
    id: str
    status: MonitorStatus
    timeout: int
    alert_email: str
    time_remaining: Optional[float] = Field(
        None,
        description="Approximate seconds remaining before alert fires. None if paused or down.",
    )