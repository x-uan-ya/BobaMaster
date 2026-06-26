import logging
from uuid import UUID, uuid4
from datetime import datetime, timezone, timedelta
from typing import Optional

from app.models.inventory import (
    PreparedBatch,
    BrewStartRequest,
    BrewCompleteRequest,
    RecalibrateRequest,
    WasteLogRequest,
    InventoryStateResponse,
)
from app.services.inventory_service import InventoryService

logger = logging.getLogger("BobaMaster.InventoryAgent")

# ---------------------------------------------------------------------------
# Business Constants — shelf lives in minutes, set by operations management.
# These values are deterministic and must NOT be altered by LLM reasoning.
# ---------------------------------------------------------------------------
SHELF_LIFE_MINUTES: dict[str, int] = {
    "tapioca_pearls": 240,    # 4 hours once cooked
    "black_tea": 360,         # 6 hours once brewed
    "jasmine_tea": 360,
    "oolong_tea": 360,
    "thai_tea": 360,
    "earl_grey_tea": 360,
    "milk": 480,              # 8 hours refrigerated
    "coconut_milk": 480,
    "soy_milk": 480,
    "taro_powder": 480,       # mixed paste, refrigerated
}
DEFAULT_SHELF_LIFE_MINUTES = 360


def _shelf_life(ingredient_id: str) -> int:
    return SHELF_LIFE_MINUTES.get(ingredient_id, DEFAULT_SHELF_LIFE_MINUTES)


# ---------------------------------------------------------------------------
# InventoryAgent
# ---------------------------------------------------------------------------

class InventoryAgent:
    """
    Deterministic inventory ledger. Manages the lifecycle of prepared
    ingredient batches through cooking, active usage, and expiry.

    Strictly no LLM calls — all arithmetic is performed in pure Python.
    """

    def __init__(self, service: InventoryService):
        self._svc = service

    # ------------------------------------------------------------------
    # Brew Lifecycle
    # ------------------------------------------------------------------

    def start_brew(self, req: BrewStartRequest) -> PreparedBatch:
        """Register that a batch has started cooking. Batch is NOT yet usable."""
        batch = PreparedBatch(
            batch_id=uuid4(),
            shop_id=req.shop_id,
            ingredient_id=req.ingredient_id,
            initial_qty=req.initial_qty_grams,
            remaining_qty=req.initial_qty_grams,
            started_at=datetime.now(timezone.utc),
            completed_at=None,
            expires_at=None,
        )
        self._svc.save_batch(batch)
        self._svc.mark_batch_brewing(batch)
        logger.info(f"Brew STARTED: {batch.batch_id} | {req.ingredient_id} | {req.initial_qty_grams}g")
        return batch

    def complete_brew(self, req: BrewCompleteRequest) -> PreparedBatch:
        """Mark a brew as completed. Starts the expiry countdown."""
        batch = self._svc.get_batch(req.shop_id, req.ingredient_id, req.batch_id)
        if not batch:
            raise ValueError(f"Batch {req.batch_id} not found for {req.ingredient_id}.")
        if batch.completed_at is not None:
            raise ValueError(f"Batch {req.batch_id} is already completed.")

        now = datetime.now(timezone.utc)
        shelf_mins = _shelf_life(req.ingredient_id)
        batch.completed_at = now
        batch.expires_at = now + timedelta(minutes=shelf_mins)

        self._svc.save_batch(batch)
        self._svc.mark_batch_active(batch)
        logger.info(
            f"Brew COMPLETED: {batch.batch_id} | {req.ingredient_id} | "
            f"expires at {batch.expires_at.isoformat()}"
        )
        return batch

    # ------------------------------------------------------------------
    # Deduction (FIFO)
    # ------------------------------------------------------------------

    def apply_deductions(
        self,
        shop_id: UUID,
        ingredient_id: str,
        total_deduction_qty: float,
    ) -> None:
        """
        Deduct ingredient quantity from active batches using FIFO ordering
        (oldest expiry batch first). Logs a STOCKOUT warning if deduction
        exceeds total available stock.
        """
        batches = self._svc.get_active_batches(shop_id, ingredient_id)
        remaining_to_deduct = round(total_deduction_qty, 2)

        for batch in batches:
            if remaining_to_deduct <= 0:
                break

            if batch.remaining_qty >= remaining_to_deduct:
                batch.remaining_qty = round(batch.remaining_qty - remaining_to_deduct, 2)
                remaining_to_deduct = 0.0
            else:
                remaining_to_deduct = round(remaining_to_deduct - batch.remaining_qty, 2)
                batch.remaining_qty = 0.0
                # Exhausted batch — remove from active pool
                self._svc.remove_batch(shop_id, ingredient_id, batch.batch_id)
                logger.debug(f"Batch {batch.batch_id} fully exhausted and removed.")

            self._svc.save_batch(batch)

        if remaining_to_deduct > 0:
            logger.warning(
                f"STOCKOUT: {ingredient_id} for shop {shop_id} | "
                f"Deficit: {remaining_to_deduct}g/ml after exhausting all active batches."
            )

    # ------------------------------------------------------------------
    # Manual Operations
    # ------------------------------------------------------------------

    def recalibrate(self, req: RecalibrateRequest) -> tuple[float, float]:
        """
        Override estimated inventory total with a physical audit value.
        Distributes the new total across active batches proportionally.
        Returns (previous_total, new_total).
        """
        batches = self._svc.get_active_batches(req.shop_id, req.ingredient_id)
        previous_total = round(sum(b.remaining_qty for b in batches), 2)

        if not batches:
            logger.warning(
                f"Recalibrate called for {req.ingredient_id} (shop {req.shop_id}) "
                f"but no active batches exist."
            )
            return previous_total, req.actual_qty_grams

        # Distribute the audited total proportionally across active batches
        # Preserves relative batch proportions while updating to real-world value
        if previous_total > 0:
            scale_factor = req.actual_qty_grams / previous_total
            for batch in batches:
                batch.remaining_qty = round(batch.remaining_qty * scale_factor, 2)
                self._svc.save_batch(batch)
        else:
            # All batches were empty — assign full calibrated value to newest batch
            newest = sorted(batches, key=lambda b: b.started_at, reverse=True)[0]
            newest.remaining_qty = round(req.actual_qty_grams, 2)
            self._svc.save_batch(newest)

        logger.info(
            f"Recalibrated {req.ingredient_id} for shop {req.shop_id}: "
            f"{previous_total}g → {req.actual_qty_grams}g"
        )
        return previous_total, req.actual_qty_grams

    def log_waste(self, req: WasteLogRequest) -> PreparedBatch:
        """Manually deduct a waste quantity from a specific batch (early discard)."""
        batch = self._svc.get_batch(req.shop_id, req.ingredient_id, req.batch_id)
        if not batch:
            raise ValueError(f"Batch {req.batch_id} not found.")

        waste = min(req.waste_qty_grams, batch.remaining_qty)
        batch.remaining_qty = round(batch.remaining_qty - waste, 2)
        self._svc.save_batch(batch)

        if batch.remaining_qty == 0:
            self._svc.remove_batch(req.shop_id, req.ingredient_id, req.batch_id)
            logger.info(f"Batch {req.batch_id} fully wasted and removed.")
        else:
            logger.info(
                f"Waste logged for {req.ingredient_id}: {waste}g | "
                f"Remaining: {batch.remaining_qty}g"
            )
        return batch

    # ------------------------------------------------------------------
    # State Query
    # ------------------------------------------------------------------

    def get_inventory_state(
        self,
        shop_id: UUID,
        ingredient_id: str,
    ) -> InventoryStateResponse:
        active_batches = self._svc.get_active_batches(shop_id, ingredient_id)
        brewing_batches = self._svc.get_brewing_batches(shop_id, ingredient_id)

        total_remaining = round(sum(b.remaining_qty for b in active_batches), 2)
        active_brewing_qty = round(sum(b.initial_qty for b in brewing_batches), 2)

        nearest_expiry: Optional[datetime] = None
        if active_batches:
            nearest_expiry = min(b.expires_at for b in active_batches if b.expires_at)

        return InventoryStateResponse(
            shop_id=shop_id,
            ingredient_id=ingredient_id,
            total_remaining_grams=total_remaining,
            active_batches=active_batches,
            active_brewing_qty_grams=active_brewing_qty,
            nearest_expiry=nearest_expiry,
        )

    # ------------------------------------------------------------------
    # Expiry Sweeper (called by background scheduler)
    # ------------------------------------------------------------------

    def sweep_expired_batches(self, shop_id: UUID, ingredient_id: str) -> int:
        """
        Remove all expired batches for an ingredient and return how many were swept.
        Should be called periodically (every 60s) by a background task.
        """
        expired_ids = self._svc.get_expired_batch_ids(shop_id, ingredient_id)
        swept = 0
        for bid_str in expired_ids:
            bid = UUID(bid_str)
            batch = self._svc.get_batch(shop_id, ingredient_id, bid)
            if batch and batch.remaining_qty > 0:
                logger.warning(
                    f"EXPIRED WASTE: {ingredient_id} batch {bid} | "
                    f"Discarding {batch.remaining_qty}g/ml"
                )
            self._svc.remove_batch(shop_id, ingredient_id, bid)
            swept += 1

        if swept:
            logger.info(f"Expiry sweep: {swept} expired batch(es) removed for {ingredient_id}.")
        return swept
