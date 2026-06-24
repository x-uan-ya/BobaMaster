from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import List, Literal

class POSItem(BaseModel):
    name: str = Field(..., description="Base drink name (e.g. 'Classic Milk Tea')")
    quantity: int = Field(..., gt=0, description="Quantity sold")
    size: Literal["S", "M", "L"] = Field("M", description="Drink Size")
    ice_level: Literal["normal ice", "less ice", "no ice"] = Field("normal ice", description="Ice portion level")
    modifiers: List[str] = Field(default_factory=list, description="Topping modifiers: e.g. ['extra pearls']")

class POSWebhookPayload(BaseModel):
    transaction_id: str
    shop_id: UUID
    timestamp: datetime
    items: List[POSItem]

class IngredientDeduction(BaseModel):
    ingredient_id: str
    qty_grams_ml: float

class POSWebhookResponse(BaseModel):
    status: str = "success"
    transaction_id: str
    deductions: List[IngredientDeduction]
