import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.pos import router as pos_router
from app.api.inventory import router as inventory_router
from app.api.context import router as context_router
from app.api.forecast import router as forecast_router
from app.api.operations import router as operations_router
from app.api.feedback import router as feedback_router
from app.api.websocket import ws_router, dispatcher_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger("BobaMaster.Main")

app = FastAPI(
    title="BobaMaster Operations Platform",
    description="Deterministic Operations Ledger and AI Reasoning Copilot for Bubble Tea Shops.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Attach API routers
app.include_router(pos_router, prefix="/api/v1/pos", tags=["POS Ingestion"])
app.include_router(inventory_router, prefix="/api/v1/inventory", tags=["Inventory Management"])
app.include_router(context_router, prefix="/api/v1/context", tags=["Context Enrichment"])
app.include_router(forecast_router, prefix="/api/v1/forecast", tags=["Demand Forecasting"])
app.include_router(operations_router, prefix="/api/v1/operations", tags=["Operations Decisions"])
app.include_router(feedback_router, prefix="/api/v1/feedback", tags=["Feedback"])
app.include_router(dispatcher_router, prefix="/api/v1/dispatcher", tags=["Dispatcher & Alerts"])
app.include_router(ws_router)   # WebSocket — no prefix, mounts at /ws/shop/{shop_id}


@app.get("/health", tags=["Telemetry"])
async def health_check():
    return {"status": "healthy", "service": "BobaMaster Backend"}


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting BobaMaster Backend Server...")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
