import json
import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException, status
from app.models.pos import POSWebhookPayload, POSWebhookResponse
from app.agents.decompo_agent import DecompoAgent
from app.agents.inventory_agent import InventoryAgent
from app.services.inventory_service import InventoryService
from app.services.redis_client import get_redis_client

logger = logging.getLogger("BobaMaster.API.POS")
router = APIRouter()

decompo_agent = DecompoAgent()
_redis_client = get_redis_client()
_inventory_service = InventoryService(_redis_client)
_inventory_agent = InventoryAgent(_inventory_service)

_RECIPES_PATH = Path(__file__).resolve().parents[1] / "config" / "recipes.json"


@router.get(
    "/recipes",
    status_code=status.HTTP_200_OK,
    summary="Get recipe configuration",
    description="Returns the full recipes.json bill-of-materials used by DecompoAgent.",
)
async def get_recipes():
    try:
        with open(_RECIPES_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/webhook",
    response_model=POSWebhookResponse,
    status_code=status.HTTP_200_OK,
    summary="Ingest POS Webhook Orders",
    description="Receives transaction webhooks from POS systems and decomposes items to raw inventory deductions."
)
async def pos_webhook(payload: POSWebhookPayload):
    from app.api.websocket import broadcast_inventory_update
    
    logger.info(f"Received POS Webhook for Transaction: {payload.transaction_id} (Shop: {payload.shop_id})")
    try:
        # Step 1: Decompose the items into raw ingredients
        deductions = decompo_agent.decompose_payload(payload)
        
        logger.debug(f"Resolved deductions for {payload.transaction_id}: {[d.model_dump() for d in deductions]}")
        
        # Step 2: Apply deductions to inventory (FIFO consumption)
        for deduction in deductions:
            _inventory_agent.apply_deductions(
                payload.shop_id,
                deduction.ingredient_id,
                deduction.qty_grams_ml
            )
            logger.info(f"Deducted {deduction.qty_grams_ml}g from {deduction.ingredient_id}")
            
            # Step 3: Broadcast inventory update to all connected KDS tablets
            try:
                state = _inventory_agent.get_inventory_state(payload.shop_id, deduction.ingredient_id)
                await broadcast_inventory_update(str(payload.shop_id), state)
            except Exception as e:
                logger.warning(f"Failed to broadcast inventory update: {e}")
        
        return POSWebhookResponse(
            status="success",
            transaction_id=payload.transaction_id,
            deductions=deductions
        )
    except Exception as e:
        logger.error(f"Error processing POS webhook transaction {payload.transaction_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Decomposition error: {str(e)}"
        )
