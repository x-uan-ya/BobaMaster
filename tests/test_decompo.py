import sys
import os
from uuid import uuid4
from datetime import datetime, timezone


# Guarantee backend directory is in path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

from app.models.pos import POSItem, POSWebhookPayload
from app.agents.decompo_agent import DecompoAgent

# Initialize agent pointing to config recipes
recipes_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend/app/config/recipes.json"))
agent = DecompoAgent(recipes_path=recipes_dir)

def test_standard_decomposition():
    item = POSItem(
        name="Classic Milk Tea",
        quantity=1,
        size="M",
        ice_level="normal ice",
        modifiers=[]
    )
    deductions = agent.decompose_item(item)
    
    # Assert counts: pearls (40g), black_tea (200ml), fructose (25g)
    results = {d.ingredient_id: d.qty_grams_ml for d in deductions}
    assert results["tapioca_pearls"] == 40.0
    assert results["black_tea"] == 200.0
    assert results["fructose"] == 25.0

def test_size_scaling():
    # Small size scaling (0.7x)
    item_small = POSItem(name="Classic Milk Tea", quantity=1, size="S", ice_level="normal ice")
    ded_small = {d.ingredient_id: d.qty_grams_ml for d in agent.decompose_item(item_small)}
    assert ded_small["tapioca_pearls"] == round(40.0 * 0.7, 2)
    assert ded_small["black_tea"] == round(200.0 * 0.7, 2)

    # Large size scaling (1.4x)
    item_large = POSItem(name="Classic Milk Tea", quantity=1, size="L", ice_level="normal ice")
    ded_large = {d.ingredient_id: d.qty_grams_ml for d in agent.decompose_item(item_large)}
    assert ded_large["tapioca_pearls"] == round(40.0 * 1.4, 2)
    assert ded_large["black_tea"] == round(200.0 * 1.4, 2)

def test_ice_scaling():
    # Less Ice (1.15x for liquids)
    item_less_ice = POSItem(name="Classic Milk Tea", quantity=1, size="M", ice_level="less ice")
    ded_less = {d.ingredient_id: d.qty_grams_ml for d in agent.decompose_item(item_less_ice)}
    assert ded_less["black_tea"] == round(200.0 * 1.15, 2)
    assert ded_less["tapioca_pearls"] == 40.0 # Non-liquid, stays unchanged
    
    # No Ice (1.30x for liquids)
    item_no_ice = POSItem(name="Classic Milk Tea", quantity=1, size="M", ice_level="no ice")
    ded_no = {d.ingredient_id: d.qty_grams_ml for d in agent.decompose_item(item_no_ice)}
    assert ded_no["black_tea"] == round(200.0 * 1.30, 2)

def test_extra_pearls_modifier():
    item = POSItem(
        name="Classic Milk Tea",
        quantity=1,
        size="M",
        ice_level="normal ice",
        modifiers=["extra pearls"]
    )
    ded = {d.ingredient_id: d.qty_grams_ml for d in agent.decompose_item(item)}
    assert ded["tapioca_pearls"] == round(40.0 * 1.5, 2) # 60g

def test_no_pearls_modifier():
    item = POSItem(
        name="Classic Milk Tea",
        quantity=1,
        size="M",
        ice_level="normal ice",
        modifiers=["no pearls"]
    )
    ded = {d.ingredient_id: d.qty_grams_ml for d in agent.decompose_item(item)}
    assert ded["tapioca_pearls"] == 0.0

def test_unrecognized_item():
    item = POSItem(name="Unknown Mystic Drink", quantity=1, size="M", ice_level="normal ice")
    ded = agent.decompose_item(item)
    assert len(ded) == 0

def test_grouped_aggregation():
    payload = POSWebhookPayload(
        transaction_id="tx_112",
        shop_id=uuid4(),
        timestamp=datetime.now(timezone.utc),
        items=[
            # 2x Classic Milk Tea S, normal ice
            # 1x Classic Milk Tea M, no ice, extra pearls
            POSItem(name="Classic Milk Tea", quantity=2, size="S", ice_level="normal ice"),
            POSItem(name="Classic Milk Tea", quantity=1, size="M", ice_level="no ice", modifiers=["extra pearls"])
        ]
    )
    aggregated = agent.decompose_payload(payload)
    results = {d.ingredient_id: d.qty_grams_ml for d in aggregated}

    # Calculation checks:
    # Pearls S (40g * 0.70 = 28g * 2 = 56g) + Pearls M extra (40g * 1.0 * 1.5 = 60g * 1 = 60g) = 116g
    # Tea S (200ml * 0.70 = 140ml * 2 = 280ml) + Tea M no ice (200ml * 1.0 * 1.30 = 260ml * 1 = 260ml) = 540ml
    # Fructose S (25g * 0.70 = 17.5g * 2 = 35g) + Fructose M (25g * 1.0 = 25g * 1 = 25g) = 60g
    assert results["tapioca_pearls"] == 116.0
    assert results["black_tea"] == 540.0
    assert results["fructose"] == 60.0
