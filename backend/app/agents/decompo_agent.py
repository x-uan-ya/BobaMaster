import os
import json
import logging
from typing import List, Dict
from app.models.pos import POSItem, POSWebhookPayload, IngredientDeduction

logger = logging.getLogger("BobaMaster.DecompoAgent")

class DecompoAgent:
    def __init__(self, recipes_path: str = None):
        if recipes_path is None:
            # Locate recipes.json relative to this file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            recipes_path = os.path.join(current_dir, "..", "config", "recipes.json")
            
        self.recipes_path = recipes_path
        self.recipes_data = self._load_recipes()
        
        self.liquids = set(self.recipes_data.get("liquids", []))
        self.size_multipliers = self.recipes_data.get("size_multipliers", {})
        self.ice_multipliers = self.recipes_data.get("ice_multipliers", {})
        self.recipes = self.recipes_data.get("recipes", {})

    def _load_recipes(self) -> Dict:
        try:
            with open(self.recipes_path, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load recipes file at {self.recipes_path}: {e}")
            # Fallback minimum configuration
            return {"liquids": [], "size_multipliers": {"S": 0.7, "M": 1.0, "L": 1.4}, "ice_multipliers": {"normal ice": 1.0, "less ice": 1.15, "no ice": 1.3}, "recipes": {}}

    def decompose_item(self, item: POSItem) -> List[IngredientDeduction]:
        deductions = []
        drink_name = item.name
        
        if drink_name not in self.recipes:
            logger.warning(f"Unrecognized drink item sold: '{drink_name}'. Skipping recipe decomposition.")
            return deductions

        base_recipe = self.recipes[drink_name]
        size_mult = self.size_multipliers.get(item.size, 1.0)
        ice_mult = self.ice_multipliers.get(item.ice_level, 1.0)

        for ingredient, base_portion in base_recipe.items():
            # 1. Base portion scaling by size
            portion = base_portion * size_mult

            # 2. Ice level adjustment for liquids
            if ingredient in self.liquids:
                portion = portion * ice_mult

            # 3. Handle topping modifier rules
            if ingredient == "tapioca_pearls":
                has_extra = any(mod in item.modifiers for mod in ["extra pearls", "extra tapioca"])
                has_none = any(mod in item.modifiers for mod in ["no pearls", "no tapioca"])
                if has_none:
                    portion = 0.0
                elif has_extra:
                    portion = portion * 1.5

            # 4. Multiply by item sale quantity
            total_qty = round(portion * item.quantity, 2)
            
            deductions.append(
                IngredientDeduction(ingredient_id=ingredient, qty_grams_ml=total_qty)
            )

        return deductions

    def decompose_payload(self, payload: POSWebhookPayload) -> List[IngredientDeduction]:
        aggregated: Dict[str, float] = {}

        for item in payload.items:
            item_deductions = self.decompose_item(item)
            for ded in item_deductions:
                aggregated[ded.ingredient_id] = aggregated.get(ded.ingredient_id, 0.0) + ded.qty_grams_ml

        # Convert back to structured IngredientDeduction models
        return [
            IngredientDeduction(ingredient_id=ing_id, qty_grams_ml=round(qty, 2))
            for ing_id, qty in aggregated.items()
        ]
