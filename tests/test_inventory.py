import sys
import os
import time
from uuid import uuid4, UUID
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch

# Guarantee backend is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

from app.models.inventory import (
    BrewStartRequest, BrewCompleteRequest,
    RecalibrateRequest, WasteLogRequest, PreparedBatch,
)
from app.agents.inventory_agent import InventoryAgent
from app.services.inventory_service import InventoryService

# ---------------------------------------------------------------------------
# In-memory Redis mock for unit tests (no live Redis needed)
# ---------------------------------------------------------------------------

class InMemoryStore:
    """Minimal dict-based Redis substitute for unit testing."""
    def __init__(self):
        self._hashes: dict[str, dict] = {}
        self._zsets: dict[str, dict[str, float]] = {}

    def hset(self, key, mapping=None, **kwargs):
        if key not in self._hashes:
            self._hashes[key] = {}
        if mapping:
            self._hashes[key].update(mapping)

    def hgetall(self, key):
        return self._hashes.get(key, {})

    def zadd(self, key, mapping):
        if key not in self._zsets:
            self._zsets[key] = {}
        self._zsets[key].update(mapping)

    def zrem(self, key, *members):
        if key in self._zsets:
            for m in members:
                self._zsets[key].pop(m, None)

    def zrange(self, key, start, end):
        if key not in self._zsets:
            return []
        items = sorted(self._zsets[key].items(), key=lambda x: x[1])
        if end == -1:
            return [m.encode() for m, _ in items[start:]]
        return [m.encode() for m, _ in items[start:end+1]]

    def zrangebyscore(self, key, min_score, max_score):
        if key not in self._zsets:
            return []
        max_ts = float("inf") if max_score == "+inf" else float(max_score)
        return [
            m.encode() for m, score in sorted(self._zsets[key].items(), key=lambda x: x[1])
            if float(min_score) <= score <= max_ts
        ]

    def delete(self, *keys):
        for k in keys:
            self._hashes.pop(k, None)
            self._zsets.pop(k, None)

    def pipeline(self, transaction=True):
        return PipelineStub(self)


class PipelineStub:
    def __init__(self, store: InMemoryStore):
        self._store = store
        self._ops = []

    def zadd(self, key, mapping):
        self._ops.append(("zadd", key, mapping))
        return self

    def zrem(self, key, *members):
        self._ops.append(("zrem", key, members))
        return self

    def delete(self, *keys):
        self._ops.append(("delete", keys))
        return self

    def execute(self):
        for op in self._ops:
            if op[0] == "zadd":
                self._store.zadd(op[1], op[2])
            elif op[0] == "zrem":
                self._store.zrem(op[1], *op[2])
            elif op[0] == "delete":
                self._store.delete(*op[1])


def _make_agent():
    store = InMemoryStore()
    svc = InventoryService(store)
    return InventoryAgent(svc), store


SHOP_ID = uuid4()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_brew_lifecycle():
    """Start → Complete a brew and verify expiry is set correctly."""
    agent, _ = _make_agent()

    start_req = BrewStartRequest(
        shop_id=SHOP_ID,
        ingredient_id="tapioca_pearls",
        initial_qty_grams=2000.0
    )
    batch = agent.start_brew(start_req)

    assert batch.completed_at is None
    assert batch.expires_at is None
    assert batch.remaining_qty == 2000.0

    complete_req = BrewCompleteRequest(
        batch_id=batch.batch_id,
        shop_id=SHOP_ID,
        ingredient_id="tapioca_pearls"
    )
    completed = agent.complete_brew(complete_req)

    assert completed.completed_at is not None
    assert completed.expires_at is not None
    # Pearls shelf life = 240 min; expires_at should be ~240 min after now
    delta_mins = (completed.expires_at - completed.completed_at).total_seconds() / 60
    assert abs(delta_mins - 240) < 1


def test_fifo_deduction():
    """Deduct across two batches, consuming oldest first."""
    agent, _ = _make_agent()

    # Create and activate batch 1 (expires sooner)
    b1_req = BrewStartRequest(shop_id=SHOP_ID, ingredient_id="tapioca_pearls", initial_qty_grams=1000.0)
    b1 = agent.start_brew(b1_req)
    c1 = BrewCompleteRequest(batch_id=b1.batch_id, shop_id=SHOP_ID, ingredient_id="tapioca_pearls")
    agent.complete_brew(c1)

    # Small delay so batch 2 has a later expires_at score
    time.sleep(0.05)

    # Create and activate batch 2 (expires later)
    b2_req = BrewStartRequest(shop_id=SHOP_ID, ingredient_id="tapioca_pearls", initial_qty_grams=1000.0)
    b2 = agent.start_brew(b2_req)
    c2 = BrewCompleteRequest(batch_id=b2.batch_id, shop_id=SHOP_ID, ingredient_id="tapioca_pearls")
    agent.complete_brew(c2)

    # Deduct 1200g — should exhaust batch 1 (1000g) and take 200g from batch 2
    agent.apply_deductions(SHOP_ID, "tapioca_pearls", 1200.0)

    state = agent.get_inventory_state(SHOP_ID, "tapioca_pearls")
    assert state.total_remaining_grams == 800.0
    assert len(state.active_batches) == 1  # batch 1 exhausted


def test_stockout_warning(caplog):
    """Deduct more than available stock and verify STOCKOUT warning is logged."""
    import logging
    agent, _ = _make_agent()

    b_req = BrewStartRequest(shop_id=SHOP_ID, ingredient_id="black_tea", initial_qty_grams=500.0)
    b = agent.start_brew(b_req)
    agent.complete_brew(BrewCompleteRequest(batch_id=b.batch_id, shop_id=SHOP_ID, ingredient_id="black_tea"))

    with caplog.at_level(logging.WARNING, logger="BobaMaster.InventoryAgent"):
        agent.apply_deductions(SHOP_ID, "black_tea", 800.0)

    assert any("STOCKOUT" in r.message for r in caplog.records)


def test_recalibration():
    """Staff audit overrides estimated stock proportionally."""
    agent, _ = _make_agent()

    b_req = BrewStartRequest(shop_id=SHOP_ID, ingredient_id="jasmine_tea", initial_qty_grams=2000.0)
    b = agent.start_brew(b_req)
    agent.complete_brew(BrewCompleteRequest(batch_id=b.batch_id, shop_id=SHOP_ID, ingredient_id="jasmine_tea"))

    # System says 2000ml; staff audit says 2400ml (e.g., a previous batch not logged)
    prev, new = agent.recalibrate(RecalibrateRequest(
        shop_id=SHOP_ID,
        ingredient_id="jasmine_tea",
        actual_qty_grams=2400.0
    ))

    assert prev == 2000.0
    state = agent.get_inventory_state(SHOP_ID, "jasmine_tea")
    assert abs(state.total_remaining_grams - 2400.0) < 0.1


def test_waste_logging():
    """Staff discards part of a batch; remaining quantity decreases accordingly."""
    agent, _ = _make_agent()

    b_req = BrewStartRequest(shop_id=SHOP_ID, ingredient_id="oolong_tea", initial_qty_grams=1500.0)
    b = agent.start_brew(b_req)
    agent.complete_brew(BrewCompleteRequest(batch_id=b.batch_id, shop_id=SHOP_ID, ingredient_id="oolong_tea"))

    agent.log_waste(WasteLogRequest(
        batch_id=b.batch_id,
        shop_id=SHOP_ID,
        ingredient_id="oolong_tea",
        waste_qty_grams=400.0
    ))

    state = agent.get_inventory_state(SHOP_ID, "oolong_tea")
    assert state.total_remaining_grams == 1100.0


def test_expiry_sweep():
    """Manually set a batch expiry to the past and verify sweep removes it."""
    agent, store = _make_agent()

    b_req = BrewStartRequest(shop_id=SHOP_ID, ingredient_id="tapioca_pearls", initial_qty_grams=800.0)
    b = agent.start_brew(b_req)
    b_done = agent.complete_brew(
        BrewCompleteRequest(batch_id=b.batch_id, shop_id=SHOP_ID, ingredient_id="tapioca_pearls")
    )

    # Manually override expires_at to 1 second in the past in the Redis store
    past_expiry = datetime.now(timezone.utc) - timedelta(seconds=1)
    b_done.expires_at = past_expiry
    agent._svc.save_batch(b_done)

    # Also update the sorted set score so get_expired_batch_ids finds it
    active_key = f"batches:active:{SHOP_ID}:tapioca_pearls"
    store.zadd(active_key, {str(b_done.batch_id): past_expiry.timestamp()})

    swept = agent.sweep_expired_batches(SHOP_ID, "tapioca_pearls")
    assert swept == 1

    state = agent.get_inventory_state(SHOP_ID, "tapioca_pearls")
    assert state.total_remaining_grams == 0.0
