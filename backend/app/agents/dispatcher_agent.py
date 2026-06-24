"""
DispatcherAgent — Gemini Explanation & WebSocket Broadcast (Milestone 7)

Responsibilities
────────────────
1. Receive an AlertPayload from OpsDeciderAgent.
2. Call Gemini 1.5 Flash to generate a structured LLMExplanation.
3. Compose a DispatchMessage and broadcast it to all connected WebSocket clients.

Design decisions
────────────────
• Gemini is called via the google-genai SDK (v2.x).  The client is injected so
  tests can substitute a mock without monkeypatching globals.
• Retry logic: up to MAX_RETRIES attempts with exponential back-off before
  falling back to a deterministic template string.  The `llm_used` flag in the
  DispatchMessage tells the frontend whether it received real LLM output.
• JSON response is requested via response_mime_type="application/json" and
  parsed into LLMExplanation.  Any parse failure also triggers the fallback.
• The WebSocket connection manager is injected so the agent is unit-testable
  without live sockets.
"""

from __future__ import annotations

import json
import logging
import os
import asyncio
from datetime import datetime, timezone
from typing import Optional, Protocol, runtime_checkable

import google.genai as genai
import google.genai.types as genai_types

from app.models.dispatcher import AlertPayload, DispatchMessage, LLMExplanation
from app.models.ops_decider import DecisionAction

logger = logging.getLogger("BobaMaster.DispatcherAgent")

# ──────────────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────────────

MODEL_ID       = "gemini-1.5-flash"
MAX_RETRIES    = 3
RETRY_BASE_S   = 1.0   # seconds; doubles each retry

_PROMPT_TEMPLATE = """\
You are an operations assistant for a bubble tea shop kitchen display system.
Generate a brief, actionable operational alert for kitchen staff.

Current situation:
- Ingredient: {ingredient_id}
- Decision: {action}
- Current stock: {current_stock_grams}g available
- Predicted demand in next {cook_time_minutes} minutes: {predicted_consumption_grams}g
- Runway after cook window: {target_runway_grams}g (safety floor: ~200g)
- Active brewing stock: {active_brewing_grams}g (not yet usable)
- Temperature: {temp_c}°C  |  Rain probability: {rain_pct}%
- School in session: {school_in_session}
{shortage_line}

Respond ONLY with a valid JSON object matching this exact schema:
{{
  "action_string": "<short imperative label for the KDS button, max 6 words>",
  "explanation_text": "<1-3 sentences, staff-facing, mention specific numbers>"
}}
"""


# ──────────────────────────────────────────────────────────────────────────────
# Broadcaster protocol — allows injecting a mock in tests
# ──────────────────────────────────────────────────────────────────────────────

@runtime_checkable
class BroadcasterProtocol(Protocol):
    async def broadcast(self, shop_id: str, message: str) -> None:
        ...


# ──────────────────────────────────────────────────────────────────────────────
# DispatcherAgent
# ──────────────────────────────────────────────────────────────────────────────

class DispatcherAgent:
    """
    Parameters
    ----------
    broadcaster:
        Object with ``async broadcast(shop_id, message)`` method.
        In production this is the WebSocketManager; in tests a mock.
    gemini_client:
        An initialised ``google.genai.Client``.  If None, the agent
        creates one using GEMINI_API_KEY from the environment.
    """

    def __init__(
        self,
        broadcaster: BroadcasterProtocol,
        gemini_client: Optional[genai.Client] = None,
    ):
        self._broadcaster = broadcaster
        # Accept None explicitly — means no API key available; fallback will always be used
        if gemini_client is not None:
            self._client: Optional[genai.Client] = gemini_client
        else:
            self._client = self._build_client()

    # ──────────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────────

    async def dispatch(self, payload: AlertPayload) -> DispatchMessage:
        """
        Generate an LLM explanation and broadcast the alert to all WebSocket
        clients connected to the shop's channel.

        Returns the DispatchMessage that was broadcast.
        """
        explanation, llm_used = await self._generate_explanation(payload)

        message = DispatchMessage(
            shop_id=payload.shop_id,
            ingredient_id=payload.ingredient_id,
            action=payload.action,
            action_string=explanation.action_string,
            explanation_text=explanation.explanation_text,
            current_stock_grams=payload.current_stock_grams,
            predicted_consumption_grams=payload.predicted_consumption_grams,
            target_runway_grams=payload.target_runway_grams,
            recommendation_id=payload.recommendation_id,
            predicted_shortage_at=payload.predicted_shortage_at,
            dispatched_at=datetime.now(timezone.utc),
            llm_used=llm_used,
        )

        await self._broadcaster.broadcast(
            shop_id=str(payload.shop_id),
            message=message.model_dump_json(),
        )
        logger.info(
            f"Dispatched {payload.action.value} alert for {payload.ingredient_id} "
            f"to shop {payload.shop_id} (llm_used={llm_used})"
        )
        return message

    # ──────────────────────────────────────────────────────────────────
    # LLM generation with retry + fallback
    # ──────────────────────────────────────────────────────────────────

    async def _generate_explanation(
        self, payload: AlertPayload
    ) -> tuple[LLMExplanation, bool]:
        """
        Attempt to call Gemini up to MAX_RETRIES times.
        Returns (LLMExplanation, llm_used=True) on success, or
        (fallback_explanation, llm_used=False) after exhausting retries.
        """
        prompt = self._build_prompt(payload)

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                explanation = await self._call_gemini(prompt)
                return explanation, True
            except Exception as e:
                wait = RETRY_BASE_S * (2 ** (attempt - 1))
                logger.warning(
                    f"Gemini attempt {attempt}/{MAX_RETRIES} failed: {e}. "
                    f"{'Retrying in ' + str(wait) + 's' if attempt < MAX_RETRIES else 'Using fallback.'}"
                )
                if attempt < MAX_RETRIES:
                    await asyncio.sleep(wait)

        return self._fallback_explanation(payload), False

    async def _call_gemini(self, prompt: str) -> LLMExplanation:
        """
        Make one synchronous Gemini generate_content call (run in executor to
        avoid blocking the event loop) and parse the JSON response.
        """
        if self._client is None:
            raise RuntimeError("No Gemini client available (GEMINI_API_KEY not set).")

        loop = asyncio.get_event_loop()

        def _sync_call():
            response = self._client.models.generate_content(
                model=MODEL_ID,
                contents=prompt,
                config=genai_types.GenerateContentConfig(
                    temperature=0.3,          # low temperature for consistent ops language
                    response_mime_type="application/json",
                ),
            )
            return response.text

        raw_text = await loop.run_in_executor(None, _sync_call)
        return self._parse_llm_response(raw_text)

    # ──────────────────────────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────────────────────────

    @staticmethod
    def _build_prompt(payload: AlertPayload) -> str:
        shortage_line = ""
        if payload.predicted_shortage_at:
            shortage_line = (
                f"- Estimated stockout time: "
                f"{payload.predicted_shortage_at.strftime('%H:%M')} UTC"
            )
        return _PROMPT_TEMPLATE.format(
            ingredient_id=payload.ingredient_id.replace("_", " ").title(),
            action=payload.action.value,
            current_stock_grams=payload.current_stock_grams,
            cook_time_minutes=payload.cook_time_minutes,
            predicted_consumption_grams=payload.predicted_consumption_grams,
            target_runway_grams=round(payload.target_runway_grams, 1),
            active_brewing_grams=payload.active_brewing_grams,
            temp_c=payload.temp_c,
            rain_pct=round(payload.rain_prob * 100),
            school_in_session=payload.school_in_session,
            shortage_line=shortage_line,
        )

    @staticmethod
    def _parse_llm_response(raw: str) -> LLMExplanation:
        """Parse the raw JSON string from Gemini into an LLMExplanation."""
        # Strip markdown code fences if the model adds them despite the mime type
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            lines = cleaned.splitlines()
            cleaned = "\n".join(
                line for line in lines
                if not line.strip().startswith("```")
            ).strip()
        data = json.loads(cleaned)
        return LLMExplanation.model_validate(data)

    @staticmethod
    def _fallback_explanation(payload: AlertPayload) -> LLMExplanation:
        """Deterministic fallback used when Gemini is unavailable."""
        ingredient_label = payload.ingredient_id.replace("_", " ").title()
        if payload.action == DecisionAction.BREW_NOW:
            action_string = f"Start Cooking {ingredient_label} Now"
            explanation = (
                f"Critical: only {payload.current_stock_grams}g of {ingredient_label} remaining. "
                f"Predicted demand is {payload.predicted_consumption_grams}g over the next "
                f"{payload.cook_time_minutes} minutes. Start a new batch immediately."
            )
        elif payload.action == DecisionAction.WARN:
            action_string = f"Monitor {ingredient_label} Levels"
            explanation = (
                f"Warning: {ingredient_label} stock is {payload.current_stock_grams}g. "
                f"Runway of {round(payload.target_runway_grams, 1)}g is below the recommended threshold. "
                f"Consider starting a batch soon."
            )
        else:
            action_string = f"{ingredient_label} Levels OK"
            explanation = (
                f"{ingredient_label} stock is sufficient at {payload.current_stock_grams}g. "
                f"No action required."
            )
        return LLMExplanation(action_string=action_string, explanation_text=explanation)

    @staticmethod
    def _build_client() -> Optional[genai.Client]:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.warning(
                "GEMINI_API_KEY is not set. Gemini calls will fail and the "
                "fallback explanation will be used."
            )
            return None
        return genai.Client(api_key=api_key)
