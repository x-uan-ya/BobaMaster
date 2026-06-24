/**
 * dashboardStore — Lightweight global state using React context + useReducer.
 *
 * Holds:
 *  - ingredients: latest inventory snapshot per ingredient
 *  - alerts: queue of active recommendation alerts
 *  - activeTimers: client-side brew countdowns
 *  - connectionStatus: WebSocket connection state
 */

import { createContext, useContext } from "react";
import type { Dispatch } from "react";
import type {
  InventoryIngredient,
  RecommendationAlert,
  ActiveBrewTimer,
  WsConnectionStatus,
} from "../types";

// ── State shape ────────────────────────────────────────────────────────────

export interface DashboardState {
  ingredients: Record<string, InventoryIngredient>;
  alerts: RecommendationAlert[];
  activeTimers: ActiveBrewTimer[];
  connectionStatus: WsConnectionStatus;
}

const initialState: DashboardState = {
  ingredients: {},
  alerts: [],
  activeTimers: [],
  connectionStatus: "connecting",
};

// ── Actions ────────────────────────────────────────────────────────────────

export type DashboardAction =
  | { type: "SET_CONNECTION_STATUS"; payload: WsConnectionStatus }
  | { type: "UPSERT_INGREDIENT"; payload: InventoryIngredient }
  | { type: "PUSH_ALERT"; payload: RecommendationAlert }
  | { type: "DISMISS_ALERT"; payload: string }           // payload = recommendation_id or dispatched_at
  | { type: "START_BREW_TIMER"; payload: ActiveBrewTimer }
  | { type: "REMOVE_BREW_TIMER"; payload: string };      // payload = timer id

// ── Reducer ────────────────────────────────────────────────────────────────

function dashboardReducer(
  state: DashboardState,
  action: DashboardAction
): DashboardState {
  switch (action.type) {
    case "SET_CONNECTION_STATUS":
      return { ...state, connectionStatus: action.payload };

    case "UPSERT_INGREDIENT":
      return {
        ...state,
        ingredients: {
          ...state.ingredients,
          [action.payload.ingredient_id]: action.payload,
        },
      };

    case "PUSH_ALERT": {
      // Deduplicate: don't add the same recommendation_id twice
      const exists = state.alerts.some(
        (a) =>
          a.recommendation_id &&
          a.recommendation_id === action.payload.recommendation_id
      );
      if (exists) return state;
      return { ...state, alerts: [action.payload, ...state.alerts] };
    }

    case "DISMISS_ALERT":
      return {
        ...state,
        alerts: state.alerts.filter(
          (a) =>
            a.recommendation_id !== action.payload &&
            a.dispatched_at !== action.payload
        ),
      };

    case "START_BREW_TIMER":
      return {
        ...state,
        activeTimers: [...state.activeTimers, action.payload],
      };

    case "REMOVE_BREW_TIMER":
      return {
        ...state,
        activeTimers: state.activeTimers.filter((t) => t.id !== action.payload),
      };

    default:
      return state;
  }
}

// ── Context ────────────────────────────────────────────────────────────────

interface DashboardContextValue {
  state: DashboardState;
  dispatch: Dispatch<DashboardAction>;
}

export const DashboardContext = createContext<DashboardContextValue>({
  state: initialState,
  dispatch: () => undefined,
});

export function useDashboard() {
  return useContext(DashboardContext);
}

export { dashboardReducer, initialState };
