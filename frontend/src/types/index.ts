// ── Shared domain types matching backend Pydantic schemas ──────────────────

export type DecisionAction = "BREW_NOW" | "WARN" | "WAIT";

export interface InventoryIngredient {
  ingredient_id: string;
  total_remaining_grams: number;
  active_brewing_qty_grams: number;
  nearest_expiry: string | null;   // ISO datetime string
  active_batches: PreparedBatch[];
}

export interface PreparedBatch {
  batch_id: string;
  ingredient_id: string;
  initial_qty: number;
  remaining_qty: number;
  started_at: string;
  completed_at: string | null;
  expires_at: string | null;
}

export interface RecommendationAlert {
  event_type: "recommendation_alert";
  shop_id: string;
  ingredient_id: string;
  action: DecisionAction;
  action_string: string;
  explanation_text: string;
  current_stock_grams: number;
  predicted_consumption_grams: number;
  target_runway_grams: number;
  recommendation_id: string | null;
  predicted_shortage_at: string | null;
  dispatched_at: string;
  llm_used: boolean;
}

export interface InventoryUpdate {
  event_type: "inventory_update";
  shop_id: string;
  ingredients: InventoryIngredient[];
  updated_at: string;
}

// Union type for any message received over the WebSocket
export type WsMessage = RecommendationAlert | InventoryUpdate;

export type WsConnectionStatus = "connecting" | "online" | "offline";

// ── Active brewing timer (client-side only) ────────────────────────────────
export interface ActiveBrewTimer {
  id: string;               // client-generated UUID
  batch_id: string;
  ingredient_id: string;
  started_at: number;       // Date.now() when "Start Cooking" was pressed
  cook_time_ms: number;     // e.g. 50 * 60 * 1000 for pearls
  label: string;
}
