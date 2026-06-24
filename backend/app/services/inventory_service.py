import json
import redis
import logging
from uuid import UUID
from datetime import datetime, timezone
from typing import Optional
from app.models.inventory import PreparedBatch

logger = logging.getLogger("BobaMaster.InventoryService")

# ---------------------------------------------------------------------------
# Redis Key Helpers
# ---------------------------------------------------------------------------

def _batch_key(shop_id: UUID, ingredient_id: str, batch_id: UUID) -> str:
    """Redis Hash key for a single batch's full state."""
    return f"batch:{shop_id}:{ingredient_id}:{batch_id}"


def _active_batches_key(shop_id: UUID, ingredient_id: str) -> str:
    """Redis Sorted Set key storing active batch_ids scored by expires_at (unix ts)."""
    return f"batches:active:{shop_id}:{ingredient_id}"


def _brewing_key(shop_id: UUID, ingredient_id: str) -> str:
    """Redis Sorted Set key storing in-progress (brewing) batch_ids."""
    return f"batches:brewing:{shop_id}:{ingredient_id}"


# ---------------------------------------------------------------------------
# InventoryService
# ---------------------------------------------------------------------------

class InventoryService:
    """
    Redis adapter responsible for reading and writing prepared ingredient
    batch states. All data transformations and business decisions are made
    in InventoryAgent; this class handles only persistence.
    """

    def __init__(self, redis_client: redis.Redis):
        self._r = redis_client

    # ------------------------------------------------------------------
    # Batch Writes
    # ------------------------------------------------------------------

    def save_batch(self, batch: PreparedBatch) -> None:
        key = _batch_key(batch.shop_id, batch.ingredient_id, batch.batch_id)
        payload = {
            "batch_id": str(batch.batch_id),
            "shop_id": str(batch.shop_id),
            "ingredient_id": batch.ingredient_id,
            "initial_qty": str(batch.initial_qty),
            "remaining_qty": str(batch.remaining_qty),
            "started_at": batch.started_at.isoformat(),
            "completed_at": batch.completed_at.isoformat() if batch.completed_at else "",
            "expires_at": batch.expires_at.isoformat() if batch.expires_at else "",
        }
        self._r.hset(key, mapping=payload)
        logger.debug(f"Saved batch {batch.batch_id} to Redis.")

    def mark_batch_brewing(self, batch: PreparedBatch) -> None:
        """Add batch_id to the in-progress sorted set (scored by started_at)."""
        key = _brewing_key(batch.shop_id, batch.ingredient_id)
        score = batch.started_at.timestamp()
        self._r.zadd(key, {str(batch.batch_id): score})

    def mark_batch_active(self, batch: PreparedBatch) -> None:
        """Move batch from brewing set to active set; start expiry clock."""
        brew_key = _brewing_key(batch.shop_id, batch.ingredient_id)
        active_key = _active_batches_key(batch.shop_id, batch.ingredient_id)

        pipe = self._r.pipeline(transaction=True)
        pipe.zrem(brew_key, str(batch.batch_id))
        pipe.zadd(active_key, {str(batch.batch_id): batch.expires_at.timestamp()})
        pipe.execute()
        logger.info(f"Batch {batch.batch_id} moved to active pool (expires {batch.expires_at.isoformat()}).")

    def remove_batch(self, shop_id: UUID, ingredient_id: str, batch_id: UUID) -> None:
        """Remove a batch completely from Redis (used after expiry sweep or full depletion)."""
        active_key = _active_batches_key(shop_id, ingredient_id)
        brew_key = _brewing_key(shop_id, ingredient_id)
        batch_key = _batch_key(shop_id, ingredient_id, batch_id)

        pipe = self._r.pipeline(transaction=True)
        pipe.zrem(active_key, str(batch_id))
        pipe.zrem(brew_key, str(batch_id))
        pipe.delete(batch_key)
        pipe.execute()
        logger.debug(f"Removed batch {batch_id} from Redis.")

    # ------------------------------------------------------------------
    # Batch Reads
    # ------------------------------------------------------------------

    def get_batch(self, shop_id: UUID, ingredient_id: str, batch_id: UUID) -> Optional[PreparedBatch]:
        key = _batch_key(shop_id, ingredient_id, batch_id)
        data = self._r.hgetall(key)
        if not data:
            return None
        return self._deserialize_batch(data)

    def get_active_batches(self, shop_id: UUID, ingredient_id: str) -> list[PreparedBatch]:
        """Returns active (ready-to-use, non-expired) batches sorted oldest-first (FIFO)."""
        active_key = _active_batches_key(shop_id, ingredient_id)
        now_ts = datetime.now(timezone.utc).timestamp()

        # Fetch only non-expired batch_ids from sorted set (score <= +inf, filter by now)
        batch_ids = self._r.zrangebyscore(active_key, 0, "+inf")
        batches = []
        for bid_bytes in batch_ids:
            bid = bid_bytes.decode() if isinstance(bid_bytes, bytes) else bid_bytes
            batch = self.get_batch(shop_id, ingredient_id, UUID(bid))
            if batch and batch.expires_at and batch.expires_at.timestamp() > now_ts:
                batches.append(batch)
        return batches

    def get_brewing_batches(self, shop_id: UUID, ingredient_id: str) -> list[PreparedBatch]:
        """Returns batches currently in the brewing/cooking state."""
        brew_key = _brewing_key(shop_id, ingredient_id)
        batch_ids = self._r.zrange(brew_key, 0, -1)
        batches = []
        for bid_bytes in batch_ids:
            bid = bid_bytes.decode() if isinstance(bid_bytes, bytes) else bid_bytes
            batch = self.get_batch(shop_id, ingredient_id, UUID(bid))
            if batch:
                batches.append(batch)
        return batches

    def get_expired_batch_ids(self, shop_id: UUID, ingredient_id: str) -> list[str]:
        """Returns batch_ids whose expires_at score is <= now (expired batches)."""
        active_key = _active_batches_key(shop_id, ingredient_id)
        now_ts = datetime.now(timezone.utc).timestamp()
        expired = self._r.zrangebyscore(active_key, 0, now_ts)
        return [b.decode() if isinstance(b, bytes) else b for b in expired]

    # ------------------------------------------------------------------
    # Deserializer
    # ------------------------------------------------------------------

    @staticmethod
    def _deserialize_batch(data: dict) -> PreparedBatch:
        def _decode(v):
            return v.decode() if isinstance(v, bytes) else v

        def _parse_dt(s: str) -> Optional[datetime]:
            s = _decode(s)
            return datetime.fromisoformat(s) if s else None

        return PreparedBatch(
            batch_id=UUID(_decode(data[b"batch_id"] if b"batch_id" in data else data["batch_id"])),
            shop_id=UUID(_decode(data[b"shop_id"] if b"shop_id" in data else data["shop_id"])),
            ingredient_id=_decode(data[b"ingredient_id"] if b"ingredient_id" in data else data["ingredient_id"]),
            initial_qty=float(_decode(data[b"initial_qty"] if b"initial_qty" in data else data["initial_qty"])),
            remaining_qty=float(_decode(data[b"remaining_qty"] if b"remaining_qty" in data else data["remaining_qty"])),
            started_at=_parse_dt(data[b"started_at"] if b"started_at" in data else data["started_at"]),
            completed_at=_parse_dt(data[b"completed_at"] if b"completed_at" in data else data["completed_at"]),
            expires_at=_parse_dt(data[b"expires_at"] if b"expires_at" in data else data["expires_at"]),
        )
