# Pulse-Check API — "Watchdog" Sentinel

A Dead Man's Switch API built with Python and FastAPI. Remote devices register a countdown timer and must send periodic heartbeats to prove they are alive. If a heartbeat is missed, the system automatically fires an alert.

---

## Architecture Diagram
┌─────────────────────────────────────────────────────────────┐
│                        Client / Device                       │
└───────────┬─────────────────┬────────────────┬──────────────┘
│                 │                │
POST /monitors   POST /{id}/heartbeat  POST /{id}/pause
│                 │                │
┌───────────▼─────────────────▼────────────────▼──────────────┐
│                     FastAPI Router (routes.py)               │
└───────────┬─────────────────────────────────────────────────┘
│
┌───────────▼──────────────────────────────────────────────────┐
│          In-memory store  dict[str, Monitor]  (store.py)     │
└───────────┬──────────────────────────────────────────────────┘
│
┌───────────▼──────────────────────────────────────────────────┐
│         asyncio Timer Engine  (timer.py)                     │
└───────────┬──────────────────────────────────────────────────┘
│
Monitor State Machine:
ACTIVE --heartbeat--> ACTIVE  (timer resets)
ACTIVE --pause------> PAUSED  (timer cancelled)
PAUSED --heartbeat--> ACTIVE  (timer restarts)
ACTIVE --timeout----> DOWN    (alert fires)

---

## Project Structure
pulse-check-api/
├── app/
│   ├── init.py
│   ├── main.py
│   ├── models.py
│   ├── routes.py
│   ├── store.py
│   └── timer.py
├── requirements.txt
└── README.md

---

## Setup Instructions

**Prerequisites:** Python 3.11+

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Visit http://localhost:8000/docs to see the interactive API documentation.

---

## API Documentation

### POST /monitors
Register a new device monitor and start its countdown timer.

**Request:**
```json
{
  "id": "device-123",
  "timeout": 60,
  "alert_email": "admin@critmon.com"
}
```
**Response 201:**
```json
{
  "message": "Monitor 'device-123' registered. Countdown started for 60s.",
  "id": "device-123",
  "timeout": 60,
  "status": "active"
}
```

### POST /monitors/{id}/heartbeat
Reset the countdown. If the monitor was paused, it automatically resumes.

**Response 200:**
```json
{
  "message": "Heartbeat received. Timer reset to 60s.",
  "id": "device-123",
  "status": "active"
}
```

### POST /monitors/{id}/pause
Stop the countdown without triggering an alert. Used during maintenance.

**Response 200:**
```json
{
  "message": "Monitor 'device-123' paused.",
  "id": "device-123",
  "status": "paused"
}
```

### GET /monitors/{id}
Developer's Choice — inspect the current state and time remaining.

**Response 200:**
```json
{
  "id": "device-123",
  "status": "active",
  "timeout": 60,
  "alert_email": "admin@critmon.com",
  "time_remaining": 42.3
}
```

---

## Alert Format

When a countdown expires the system logs:
```json
{
  "ALERT": "Device device-123 is down!",
  "time": "2025-04-09T10:30:00.000000+00:00",
  "alert_email": "admin@critmon.com"
}
```

---

## Developer's Choice — GET /monitors/{id}

I added a read endpoint that returns a monitor's full current state including time remaining.

**Why:** A monitoring system that cannot be queried is incomplete. Operators need to check device status proactively during incidents — not just wait for an alert to fire. This endpoint enables that workflow and demonstrates observability thinking, which is a core backend engineering concern.


