"""
Milestone 7 — DispatcherAgent Test Suite
==========================================
All tests are deterministic and require no external services.
- Gemini client is replaced with a mock that returns controllable JSON.
- WebSocket broadcaster is replaced with an in-memory capture list.
- Uses asyncio.run() for Python 3.10+ compatibility (asyncio.coroutine removed).
"""

import sys
import os
import json
import asyncio
from uuid import uuid4
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, AsyncMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

from app.models.dispatcher import AlertPayload, DispatchMessage, LLMExplanation
from app.models.ops_decider import DecisionAction
from app.agents.dispatcher_agent import DispatcherAgent


SHOP_ID = uuid4()
INGREDIENT = "tapioca_pearls"


# ──────────────────────────────────────────────────────────────────────────────
# Test infrastructure helpers
# ──────────────────────────────────────────────────────────────────────────────

class MockBroadcaster:
    """Captures broadcast calls in-memory instead of sending WebSocket frames."""

    def __init__(self):
        self.sent: list[dict] = []

    async def broadcast(self, shop_id: str, message: str) -> None:
        self.sent.append({"shop_id": shop_id, "message": message})


def _make_gemini_mock(json_payload: dict):
    """Return a mock google.genai.Client whose generate_content returns json_payload."""
    mock_response = MagicMock()
    mock_response.text = json.dumps(json_payload)

    mock_models = MagicMock()
    mock_models.generate_content.return_value = mock_response

    mock_client = MagicMock()
    mock_client.models = mock_models
    return mock_client


def _make_failing_gemini_mock(error: Exception):
    """Return a mock client that always raises the given error."""
    mock_models = MagicMock()
    mock_models.generate_content.side_effect = error

    mock_client = MagicMock()
    mock_client.models = mock_models
    return mock_client


def _brew_now_payload() -> AlertPayload:
    return AlertPayload(
        shop_id=SHOP_ID,
        ingredient_id=INGREDIENT,
        action=DecisionAction.BREW_NOW,
        current_stock_grams=400.0,
        active_brewing_grams=0.0,
        predicted_consumption_grams=2000.0,
        target_runway_grams=-1600.0,
        cook_time_minutes=50,
        temp_c=31.0,
        rain_prob=0.1,
        school_in_session=True,
        predicted_shortage_at=datetime.now(timezone.utc) + timedelta(minutes=12),
    )


# ──────────────────────────────────────────────────────────────────────────────
# 1. Successful Gemini call — dispatch returns DispatchMessage
# ──────────────────────────────────────────────────────────────────────────────

def test_dispatch_returns_dispatch_message():
    """dispatch() must return a DispatchMessage Pydantic instance."""
    broadcaster = MockBroadcaster()
    gemini_mock = _make_gemini_mock({
        "action_string": "Start Cooking Pearls Now",
        "explanation_text": "Stock is critically low at 400g. Start a new batch immediately.",
    })
    agent = DispatcherAgent(broadcaster=broadcaster, gemini_client=gemini_mock)

    result = asyncio.run(agent.dispatch(_brew_now_payload()))

    assert isinstance(result, DispatchMessage)
    assert result.shop_id == SHOP_ID
    assert result.ingredient_id == INGREDIENT
    assert result.action == DecisionAction.BREW_NOW


def test_dispatch_sets_llm_used_true_on_success():
    """llm_used must be True when Gemini responds successfully."""
    broadcaster = MockBroadcaster()
    gemini_mock = _make_gemini_mock({
        "action_string": "Cook Pearls Now",
        "explanation_text": "400g remaining, demand is 1000g.",
    })
    agent = DispatcherAgent(broadcaster=broadcaster, gemini_client=gemini_mock)
    result = asyncio.run(agent.dispatch(_brew_now_payload()))

    assert result.llm_used is True


def test_dispatch_populates_action_string_and_explanation():
    """action_string and explanation_text must come from the Gemini response."""
    broadcaster = MockBroadcaster()
    gemini_mock = _make_gemini_mock({
        "action_string": "Start Cooking Pearls Now",
        "explanation_text": "School rush in 15 mins. Only 400g left.",
    })
    agent = DispatcherAgent(broadcaster=broadcaster, gemini_client=gemini_mock)
    result = asyncio.run(agent.dispatch(_brew_now_payload()))

    assert result.action_string == "Start Cooking Pearls Now"
    assert "400g" in result.explanation_text or "rush" in result.explanation_text


# ──────────────────────────────────────────────────────────────────────────────
# 2. Broadcast is sent to the correct shop channel
# ──────────────────────────────────────────────────────────────────────────────

def test_broadcast_sent_to_correct_shop():
    """The broadcast must target the shop_id from the payload."""
    broadcaster = MockBroadcaster()
    gemini_mock = _make_gemini_mock({
        "action_string": "Cook Now",
        "explanation_text": "Low stock.",
    })
    agent = DispatcherAgent(broadcaster=broadcaster, gemini_client=gemini_mock)
    asyncio.run(agent.dispatch(_brew_now_payload()))

    assert len(broadcaster.sent) == 1
    assert broadcaster.sent[0]["shop_id"] == str(SHOP_ID)


def test_broadcast_message_is_valid_json():
    """The broadcast payload must deserialize as a valid DispatchMessage."""
    broadcaster = MockBroadcaster()
    gemini_mock = _make_gemini_mock({
        "action_string": "Cook Now",
        "explanation_text": "Low stock.",
    })
    agent = DispatcherAgent(broadcaster=broadcaster, gemini_client=gemini_mock)
    asyncio.run(agent.dispatch(_brew_now_payload()))

    raw = broadcaster.sent[0]["message"]
    parsed = DispatchMessage.model_validate_json(raw)
    assert parsed.event_type == "recommendation_alert"
    assert parsed.shop_id == SHOP_ID


# ──────────────────────────────────────────────────────────────────────────────
# 3. Gemini failure → fallback explanation
# ──────────────────────────────────────────────────────────────────────────────

async def _noop_sleep(_):
    """Async no-op replacing asyncio.sleep to skip retry delays in tests."""
    pass


def test_gemini_failure_uses_fallback_explanation():
    """When Gemini raises on every attempt, llm_used must be False."""
    broadcaster = MockBroadcaster()
    failing_mock = _make_failing_gemini_mock(RuntimeError("API rate limit"))

    with patch("app.agents.dispatcher_agent.asyncio.sleep", side_effect=_noop_sleep):
        agent = DispatcherAgent(broadcaster=broadcaster, gemini_client=failing_mock)
        result = asyncio.run(agent.dispatch(_brew_now_payload()))

    assert result.llm_used is False
    assert result.action_string != ""
    assert result.explanation_text != ""


def test_fallback_explanation_contains_stock_info():
    """The fallback explanation must reference the current stock level."""
    broadcaster = MockBroadcaster()
    failing_mock = _make_failing_gemini_mock(ConnectionError("timeout"))

    with patch("app.agents.dispatcher_agent.asyncio.sleep", side_effect=_noop_sleep):
        agent = DispatcherAgent(broadcaster=broadcaster, gemini_client=failing_mock)
        result = asyncio.run(agent.dispatch(_brew_now_payload()))

    assert "400" in result.explanation_text or "400.0" in result.explanation_text


def test_fallback_broadcast_still_sent():
    """Even when Gemini fails, a DispatchMessage must still be broadcast."""
    broadcaster = MockBroadcaster()
    failing_mock = _make_failing_gemini_mock(RuntimeError("quota exceeded"))

    with patch("app.agents.dispatcher_agent.asyncio.sleep", side_effect=_noop_sleep):
        agent = DispatcherAgent(broadcaster=broadcaster, gemini_client=failing_mock)
        asyncio.run(agent.dispatch(_brew_now_payload()))

    assert len(broadcaster.sent) == 1


# ──────────────────────────────────────────────────────────────────────────────
# 4. LLM response parsing
# ──────────────────────────────────────────────────────────────────────────────

def test_parse_llm_response_clean_json():
    """_parse_llm_response must handle a clean JSON string."""
    raw = json.dumps({
        "action_string": "Cook Pearls Now",
        "explanation_text": "Stock is critically low.",
    })
    result = DispatcherAgent._parse_llm_response(raw)
    assert isinstance(result, LLMExplanation)
    assert result.action_string == "Cook Pearls Now"


def test_parse_llm_response_strips_code_fences():
    """_parse_llm_response must strip markdown code fences the model sometimes adds."""
    raw = '```json\n{"action_string": "Cook Now", "explanation_text": "Low stock."}\n```'
    result = DispatcherAgent._parse_llm_response(raw)
    assert result.action_string == "Cook Now"


# ──────────────────────────────────────────────────────────────────────────────
# 5. WARN payload dispatch
# ──────────────────────────────────────────────────────────────────────────────

def test_dispatch_warn_action():
    """dispatch() must work correctly for WARN-level alerts."""
    broadcaster = MockBroadcaster()
    gemini_mock = _make_gemini_mock({
        "action_string": "Monitor Pearl Levels",
        "explanation_text": "Stocks are trending low. Consider starting a batch soon.",
    })
    agent = DispatcherAgent(broadcaster=broadcaster, gemini_client=gemini_mock)

    warn_payload = AlertPayload(
        shop_id=SHOP_ID,
        ingredient_id=INGREDIENT,
        action=DecisionAction.WARN,
        current_stock_grams=800.0,
        active_brewing_grams=0.0,
        predicted_consumption_grams=500.0,
        target_runway_grams=300.0,
        cook_time_minutes=50,
        temp_c=24.0,
        rain_prob=0.1,
        school_in_session=True,
    )
    result = asyncio.run(agent.dispatch(warn_payload))
    assert result.action == DecisionAction.WARN
    assert len(broadcaster.sent) == 1


# ──────────────────────────────────────────────────────────────────────────────
# 6. WebSocketManager unit tests (no network required)
# ──────────────────────────────────────────────────────────────────────────────

def test_websocket_manager_connect_and_count():
    """Connecting a mock WebSocket must increment the connection count."""
    # Import WebSocketManager directly — avoids triggering module-level singleton
    from app.api.websocket import WebSocketManager

    manager = WebSocketManager()

    async def _run():
        mock_ws = MagicMock()
        mock_ws.accept = AsyncMock()
        await manager.connect("shop-1", mock_ws)
        assert manager.connection_count("shop-1") == 1

    asyncio.run(_run())


def test_websocket_manager_disconnect_cleans_up():
    """Disconnecting must remove the WebSocket and clean up empty shop entries."""
    from app.api.websocket import WebSocketManager

    manager = WebSocketManager()

    async def _run():
        mock_ws = MagicMock()
        mock_ws.accept = AsyncMock()
        await manager.connect("shop-2", mock_ws)
        manager.disconnect("shop-2", mock_ws)
        assert manager.connection_count("shop-2") == 0
        assert "shop-2" not in manager.all_shop_ids()

    asyncio.run(_run())


def test_websocket_manager_broadcast_sends_to_all():
    """broadcast() must call send_text on every connected WebSocket for the shop."""
    from app.api.websocket import WebSocketManager

    manager = WebSocketManager()

    async def _run():
        ws_a = MagicMock()
        ws_a.accept = AsyncMock()
        ws_a.send_text = AsyncMock()

        ws_b = MagicMock()
        ws_b.accept = AsyncMock()
        ws_b.send_text = AsyncMock()

        await manager.connect("shop-3", ws_a)
        await manager.connect("shop-3", ws_b)
        await manager.broadcast("shop-3", "hello")

        ws_a.send_text.assert_called_once_with("hello")
        ws_b.send_text.assert_called_once_with("hello")

    asyncio.run(_run())
