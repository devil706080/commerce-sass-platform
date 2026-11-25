from contextlib import asynccontextmanager

from fastapi import FastAPI

from inventory.config import load_settings
from inventory.routes import router


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield


app = FastAPI(title="Inventory Service", version="0.1.0", lifespan=lifespan)
app.state.settings = load_settings()


@app.get("/health", tags=["health"])
def health(): return {"status": "ok", "service": "inventory"}


app.include_router(router)
