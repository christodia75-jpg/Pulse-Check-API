from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.routes import router
from app.store import monitor_store


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    for monitor in monitor_store.values():
        if monitor.task and not monitor.task.done():
            monitor.task.cancel()


app = FastAPI(
    title="Pulse-Check API",
    description="Dead Man's Switch API for monitoring remote devices.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(router)