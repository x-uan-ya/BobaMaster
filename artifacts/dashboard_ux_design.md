# UX Design Specification: Bobaflow Enterprise Dashboard

**Role:** Senior UX Designer  
**Design System:** Google Material Design 3 (M3)  
**Target Device:** 10.1-inch Kitchen Tablet (Landscape, WXGA 1280x800) & Desktop Manager Console  

---

## 1. Global Layout & Design System

We use a responsive layout with a **Navigation Rail** (collapsible to a Navigation Drawer on larger desktop screens) and a **Top App Bar**.

```
+------------------------------------------------------------------------------------+
|  ( = ) App Logo  |  Search POS/Brews...              (Online) [ Downtown Store v ]  |
+---+--------------------------------------------------------------------------------+
| N |                                                                                |
| a |  [ Page Title / Header Area ]                                                  |
| v |                                                                                |
|   |  +---------------------------------------+  +-------------------------------+  |
| R |  |                                       |  |                               |  |
| a |  |            Main Content Card          |  |       Side Telemetry Card     |  |
| i |  |                                       |  |                               |  |
| l |  +---------------------------------------+  +-------------------------------+  |
+---+--------------------------------------------------------------------------------+
```

### Color Palette (Material 3 Dynamic Tonal Palette)
*   **Primary (M3 Teal):** HSL(174, 62%, 15%) - Represents stability and clean operation.
*   **Secondary (Boba Brown):** HSL(28, 35%, 20%) - Visual link to tea/pearl tones.
*   **Error (Alert Crimson):** HSL(354, 70%, 42%) - High-contrast alert state.
*   **Surface / Background:** HSL(0, 0%, 98%) (Light Mode) / HSL(0, 0%, 10%) (Dark Mode).

---

## 2. Page Breakdown & Interface Specifications

### 2.1 Dashboard (Home)
An operational "control room" view designed for rapid scanning.

#### Layout Grid: 12-column grid, 3 main areas.
1.  **Critical Operations Banner (Full Width - 12 cols):**
    *   *Type:* Elevated Card (M3) with a flashing outline if `Critical` state is active.
    *   *Content:* Displays the highest priority action item. (e.g., *"Cook 1 Batch of Pearls immediately. Stock out expected at 16:45"*).
    *   *Controls:* Tonal Button `[ Start Cooking ]` and Text Button `[ Snooze 5m ]`.
2.  **Live State Cards (8 cols - Left):**
    *   *Type:* Grid of 4 Elevated Cards showing ingredient levels.
    *   *Visuals:* Circular Progress indicators showing current volume % (colored Green for stable, Yellow for warning, Red for critical).
    *   *Metadata:* Displays remaining quantity in grams/liters, batch count, and countdown to nearest batch expiry.
3.  **Active Cooking Timers (4 cols - Right):**
    *   *Type:* Outlined Card with Linear Progress Indicators.
    *   *Content:* Lists active brewing pots (e.g., *"Tapioca Pearl Batch #04 - 18 mins remaining"*).
    *   *Control:* Button to cancel or adjust timers.

---

### 2.2 Inventory Page
Ledger view for managing cooked and raw stocks.

#### UI Elements:
1.  **Prepared Batch Stack Card (FIFO View):**
    *   *Type:* Card with list item rows showing active batches.
    *   *Visualization:* Horizontal progress bars representing the age/expiry of each batch. As time runs down, the bar color shifts from Teal to Amber.
    *   *Action:* `[ Discard Batch ]` button to log early spoilage or wastage.
2.  **Manual Calibration FAB (Floating Action Button):**
    *   *Type:* Extended FAB with icon `[ + Scale Inventory ]`.
    *   *Interactions:* Opens a modal with large number pads allowing staff to quickly key in audited physical weights (e.g., *"Re-weight: 1250g"*).
3.  **Raw Inventory Stock Levels Card:**
    *   *Type:* Grid list of dry goods (e.g., unboiled tapioca bags, milk powder cartons, syrup bottles).
    *   *Data:* Current storage counts and automated restock indicators.

---

### 2.3 Forecast Page
Deep-dive predictive dashboard for managers.

#### UI Elements:
1.  **Multi-Horizon Demand Chart (8 cols):**
    *   *Type:* Interactive Line Chart (Recharts/D3 style) with three forecasting tracks:
        *   *Line A (Solid Teal):* Historical baseline sales average.
        *   *Line B (Dashed Blue):* Real-time AI prediction curve.
        *   *Line C (Shaded Area):* Actual transactions logged today.
    *   *Controls:* Interval selectors: `[ 30m ]`, `[ 60m ]`, `[ 120m ]`, `[ Custom ]`.
2.  **Context Factors Panel (4 cols):**
    *   *Type:* Elevated Card.
    *   *Content:* Icons representing weather (rain, cloud, sun), school session status, and calendar events. Hovering/tapping reveals their specific multiplier impact (e.g., *"Rain: +12% Hot milk tea demand forecast"*).

---

### 2.4 Insights Page
Plain-english operational diagnostics.

#### UI Elements:
1.  **LLM Operational Logs Feed (Vertical Feed):**
    *   *Type:* Segmented Card feed with distinct action badges (e.g., **[Anomaly Detected]**, **[Efficiency Recommendation]**).
    *   *Text Display:* A paragraph detailing the "Why" behind predictions using LLM explanation generators.
    *   *Example Card:*
        > **[Anomaly Detected] Friday School Rush Peak Shifted**  
        > *Why:* High school let out 30 minutes earlier today due to exam week schedules. The agent observed a 15-minute POS velocity spike starting at 16:00, leading to a prompt recommendation to cook 1 batch of pearls early. This action saved approximately $140 in potential lost revenue.
2.  **Staff Compliance Card:**
    *   *Type:* Bar graph showing recommendation acceptances vs rejections.
    *   *Data:* Helpful for shift reviews to check if crew are consistently ignoring warnings.

---

### 2.5 Alerts Page
Auditable history of store incidents and alarm rules.

#### UI Elements:
1.  **Split Screen Split-Pane Layout:**
    *   **Left Pane (7 cols) - Alert Log Table:**
        *   List of past warning triggers showing item, message, timestamp, status (Resolved, Ignored, Active).
        *   Filter chip buttons at top: `[ All ]` `[ Critical ]` `[ Warnings ]` `[ Resolved ]`.
    *   **Right Pane (5 cols) - Alert Threshold Settings:**
        *   Sliders and input boxes to define thresholds (e.g., *"Warn me when pearls are below X servings"*).
        *   Sound controls: dropdowns to map audio tones to alert levels.

#### Crucial Alarm & Snooze Interaction Policy:
*   **Persistent Chime:** When a critical alert is triggered, the kitchen tablet audio alarm chimes persistently at regular intervals (e.g., every 15 seconds) to guarantee audibility in a loud, active kitchen environment.
*   **No Auto-Silence:** The alarm will **never** automatically silence itself. It remains active until a crew member takes action.
*   **Acknowledge Action Paths:**
    1.  `[ Start Cooking ]`: Instantly silences the alarm, registers the action, and spawns the active brew timer.
    2.  `[ Snooze (5m / 10m) ]`: Mutes the audio for the selected period. If no brew is registered before the snooze expires, the alert chimes again at an increased volume.


---

### 2.6 Reports Page
Macro analytics for franchise managers and business owners.

#### UI Elements:
1.  **Operational Waste Dashboard (Line & Bar charts):**
    *   *Visual:* Bar chart of daily pearl/tea waste (kg/liters) overlaid with a line chart representing total product costs lost.
2.  **Financial Loss Matrix (Data Table):**
    *   Columns: Date, Ingredient, Batch Quantity, Cause (Expiry, Spillage), Total Cost Loss, AI Avoided Waste (Est).
3.  **Performance Grade Card:**
    *   *Type:* Circular Dial Gauge.
    *   *Value:* Operational efficiency score (A, B, C...) based on waste reduction, forecasting accuracy, and stockout minutes.

---

### 2.7 Settings Page
System and configuration controls.

#### UI Elements:
1.  **Recipe Matrix Editor:**
    *   *Interface:* List of menu items (e.g., *"Brown Sugar Pearl Milk Tea"*). Expanding a row shows ingredient breakdown sliders (e.g., Tapioca: 50g, Black Tea: 200ml, Fructose: 25g).
2.  **Edge-Cloud Sync Panel:**
    *   *Visuals:* Connection state graph between POS, local edge router, and cloud database.
    *   *Controls:* `[ Force Re-sync ]` and `[ Download Offline Logs ]` buttons.
3.  **API Credentials Cards:**
    *   Secure input fields to link POS provider (Square, Clover) and Notification interfaces (Slack, SMS gateways).
