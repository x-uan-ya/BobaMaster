from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional


class PreparedBatch(BaseModel):
    batch_id: UUID
    shop_id: UUID
    ingredient_id: str
    initial_qty: float
    remaining_qty: float
    started_at: datetime
    completed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    @property
    def is_brewing(self) -> bool:
        return self.completed_at is None

    @property
    def is_active(self) -> bool:
        return self.completed_at is not None and self.expires_at is not None


class BrewStartRequest(BaseModel):
    shop_id: UUID
    ingredient_id: str
    initial_qty_grams: float = Field(..., gt=0, description="Weight of batch being cooked in grams/ml")


class BrewStartResponse(BaseModel):
    batch_id: UUID
    shop_id: UUID
    ingredient_id: str
    initial_qty_grams: float
    started_at: datetime
    message: str = "Brew started successfully."


class BrewCompleteRequest(BaseModel):
    batch_id: UUID
    shop_id: UUID
    ingredient_id: str


class BrewCompleteResponse(BaseModel):
    batch_id: UUID
    ingredient_id: str
    completed_at: datetime
    expires_at: datetime
    message: str = "Brew completed. Batch is now active."


class RecalibrateRequest(BaseModel):
    shop_id: UUID
    ingredient_id: str
    actual_qty_grams: float = Field(..., ge=0, description="Audited physical weight in grams/ml")


class RecalibrateResponse(BaseModel):
    shop_id: UUID
    ingredient_id: str
    previous_total_grams: float
    new_total_grams: float
    message: str = "Inventory recalibrated successfully."


class WasteLogRequest(BaseModel):
    batch_id: UUID
    shop_id: UUID
    ingredient_id: str
    waste_qty_grams: float = Field(..., gt=0, description="Amount discarded in grams/ml")


class WasteLogResponse(BaseModel):
    batch_id: UUID
    ingredient_id: str
    waste_qty_grams: float
    remaining_qty_grams: float
    message: str = "Waste logged successfully."


class InventoryStateResponse(BaseModel):
    shop_id: UUID
    ingredient_id: str
    total_remaining_grams: float
    active_batches: list[PreparedBatch]
    active_brewing_qty_grams: float
    nearest_expiry: Optional[datetime] = None
