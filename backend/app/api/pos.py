import logging
from fastapi import APIRouter, HTTPException, status
from app.models.pos import POSWebhookPayload, POSWebhookResponse
from app.agents.decompo_agent import DecompoAgent

logger = logging.getLogger("BobaMaster.API.POS")
router = APIRouter()

# Initialize the recipe decomposition agent instance
decompo_agent = DecompoAgent()

@router.post(
    "/webhook",
    response_model=POSWebhookResponse,
    status_code=status.HTTP_200_OK,
    summary="Ingest POS Webhook Orders",
    description="Receives transaction webhooks from POS systems and decomposes items to raw inventory deductions."
)
async def pos_webhook(payload: POSWebhookPayload):
    logger.info(f"Received POS Webhook for Transaction: {payload.transaction_id} (Shop: {payload.shop_id})")
    try:
        # Decompose the items into raw ingredients
        deductions = decompo_agent.decompose_payload(payload)
        
        logger.debug(f"Resolved deductions for {payload.transaction_id}: {[d.model_dump() for d in deductions]}")
        
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
