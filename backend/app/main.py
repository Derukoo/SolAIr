import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .mqtt_ingestion import start_mqtt_listener
from .routes_data import router as data_router
from .routes_alerts import router as alerts_router
from .anomaly import start_anomaly_scheduler

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    start_mqtt_listener()
    start_anomaly_scheduler()
    yield
    # Shutdown (daemon threads clean up automatically)


app = FastAPI(title="SolAIr API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(data_router)
app.include_router(alerts_router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
