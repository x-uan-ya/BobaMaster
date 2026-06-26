# Business Intelligence Features — BobaMaster Enhancement

## Overview

BobaMaster now includes a powerful **Business Intelligence Agent** that provides store managers with real-time, actionable insights for operational decision-making.

### What It Provides

- **Revenue Forecasting** — Today's projected revenue based on current pace
- **Peak Demand Windows** — Identifies busy periods (e.g., "school rush 11am-1pm, after-work rush 5pm-7pm")
- **Top-Selling Drinks** — Which drinks are trending and which are underperforming
- **Inventory Optimization** — Specific recommendations to reduce waste and prevent stockouts
- **Staff Efficiency Metrics** — Tracks how well staff follow AI recommendations
- **Waste Analysis** — Identifies waste trends and provides corrective actions

---

## Architecture

### Backend Components

#### 1. BusinessAgent (`app/agents/business_agent.py`)
```python
class BusinessAgent:
    def get_insights(shop_id: UUID) -> BusinessInsight
        # Analyzes operational data and generates insights
        # Falls back to synthetic data when PostgreSQL is unavailable (demo mode)
```

**Key Methods:**
- `get_insights(shop_id)` — Main entry point, returns complete insight package
- `_query_database(shop_id)` — Queries PostgreSQL for real data (production)
- `_generate_demo_insights(shop_id)` — Generates realistic synthetic data (demo)

#### 2. Business Intelligence API (`app/api/business_intelligence.py`)
```
GET /api/v1/business/insights/{shop_id}
  └─ Complete business intelligence snapshot

GET /api/v1/business/revenue-forecast/{shop_id}
  └─ Daily revenue projection with current pace

GET /api/v1/business/peak-windows/{shop_id}
  └─ Historical peak demand periods
```

### Frontend Components

#### 1. BusinessInsightsPage (`src/components/BusinessInsightsPage.tsx`)
Modern, premium dashboard showing:
- **Key Metrics Row** — Revenue, waste %, staff efficiency, optimization score
- **Peak Windows Chart** — Visual bar chart of demand by hour
- **Top Drinks Table** — Ranking with trend indicators
- **Inventory Optimization Cards** — Specific, actionable recommendations

#### 2. Enhanced Dashboard
- **Quick Action Cards** — Fast access to key operations
- **Status Color Coding** — Green (healthy) → Yellow (low) → Red (critical)
- **Connection Status Indicator** — Shows if backend is online
- **Premium Styling** — Modern gradients, shadows, hover effects

---

## Insight Types

### 1. Revenue Forecasting

**Input:** Current sales pace + time remaining in operating hours  
**Output:** Projected total daily revenue

```json
{
  "current_revenue": 420,
  "current_hour": 14,
  "hours_remaining": 7,
  "avg_revenue_per_hour": 60,
  "projected_total_revenue": 840,
  "confidence": 0.85
}
```

**Use Case:**
- Store manager at 2 PM: "We're on track for $840 today (up $80 from yesterday)"
- Informs staffing decisions and promotional planning

### 2. Peak Demand Windows

**Input:** Historical sales pattern analysis  
**Output:** Identified peak periods with confidence scores

```json
{
  "peak_windows": [
    {
      "start_hour": 11,
      "end_hour": 13,
      "avg_cups_per_minute": 12.5,
      "confidence": 0.92,
      "label": "11:00 - 13:00"
    },
    {
      "start_hour": 17,
      "end_hour": 19,
      "avg_cups_per_minute": 8.3,
      "confidence": 0.88,
      "label": "17:00 - 19:00"
    }
  ]
}
```

**Use Case:**
- "Prepare extra ingredients 30 min before 11am rush"
- Allows proactive batch scheduling instead of reactive firefighting

### 3. Top-Selling Drinks

**Input:** Transaction history for the day  
**Output:** Ranked drinks with revenue and trend

```json
{
  "drink_name": "Classic Milk Tea (L)",
  "cups_sold_today": 87,
  "revenue_estimate": 522,
  "popularity_rank": 1,
  "trend": "trending_up"
}
```

**Use Case:**
- "Matcha is trending up — increase matcha powder prep from 1kg to 1.5kg"
- Identifies new customer preferences quickly

### 4. Inventory Optimization

**Input:** Current stock, forecast, waste patterns  
**Output:** Specific, actionable recommendations

```json
{
  "ingredient_id": "tapioca_pearls",
  "current_level_grams": 1200.0,
  "recommended_level_grams": 2500.0,
  "reason": "High demand for pearl drinks (trending up). Current level will deplete by 18:30 PM during evening rush.",
  "savings_potential": 150.0
}
```

**Use Case:**
- "Cook 1.3kg more pearls now (or by 4:30 PM) to avoid shortage at 6:30 PM rush"
- Specific target levels reduce both stockouts and waste

### 5. Staff Efficiency

**Input:** Recommendation acceptance rate  
**Output:** Score 0-100

```json
{
  "staff_efficiency_score": 87.5
}
```

**Use Case:**
- Track team performance over time
- Identify training needs if score drops
- Celebrate wins when score improves

---

## UI/UX Enhancements

### Premium Dashboard Design

#### Color System
- **Green** (#16a34a) — Healthy, trending up, efficient
- **Orange** (#ea580c) — Warning, low supply, needs attention
- **Red** (#b52235) — Critical, shortage, urgent action needed
- **Blue** (#0891b2) — Informational, forecasts, secondary data
- **Purple** (#7c3aed) — Analytics, insights, business intelligence

#### Visual Hierarchy
```
┌─────────────────────────────────────────────────┐
│  Operations Center              Online [●]       │
│  Real-time monitoring & recommendations          │
├─────────────────────────────────────────────────┤
│  CRITICAL ALERT BANNER (if active)              │
│  "School rush starting 14:45. Pearl stockout     │
│   forecast: 14:52. Start cooking now."          │
├─────────────────────────────────────────────────┤
│  AI CONTROLS  │ LIVE FORECAST │ INVENTORY TIPS  │
├─────────────────────────────────────────────────┤
│  QUICK ACTIONS (4 cards)                        │
│  [Log Sale] [Cook Batch] [View Forecast] ...    │
├─────────────────────────────────────────────────┤
│  INGREDIENT STATUS    │    ACTIVE TIMERS        │
│  (4 cards in grid)    │    (cooking countdowns) │
└─────────────────────────────────────────────────┘
```

#### Component Enhancements
1. **Ingredient Cards**
   - Color-coded by status (green/yellow/red)
   - Top bar indicator shows urgency
   - Hover effect for interactivity
   - Clear expiry warnings

2. **Quick Action Cards**
   - Large icons for touch-friendliness (64px minimum)
   - Scale up on hover (1.05x)
   - Color-coded by action type
   - One-click navigation

3. **Stat Cards**
   - Icon + large value + supporting text
   - Color-coded backgrounds matching the data type
   - Responsive layout (1-4 columns depending on screen)

4. **Peak Windows Chart**
   - Bar height = demand intensity
   - Opacity = confidence level
   - Labeled times and cups/min
   - Interactive (hover for details)

5. **Insights Page** 
   - Clean card-based layout
   - Color-coded recommendations
   - Specific action items (not just data)
   - Revenue projection updates live

---

## How to Use

### For Store Managers

#### Morning Routine (9 AM)
1. Open Dashboard → see overnight insights
2. View "Business Intelligence" tab
3. Check "Peak Demand Windows"
4. Prep accordingly (e.g., "Rush starts 11am, prepare extra pearls")

#### During Service
1. Keep eye on "Ingredient Status" cards
2. Notice color changes (green → yellow → red)
3. Read "Optimization Recommendations" if available
4. Act on specific suggestions ("Cook 1.3kg pearls by 4:30pm")

#### End of Day
1. Check "Staff Efficiency" score
2. Review "Top-Selling Drinks" for tomorrow's prep
3. Note waste percentage (track trends)
4. Plan tomorrow based on today's forecast

### For IT/System Admins

#### Real Data Integration (Future)
```python
# Replace _generate_demo_insights with actual queries:

def _query_database(self, shop_id: UUID):
    conn = psycopg2.connect(self.postgres_url)
    cur = conn.cursor()
    
    # Query 1: Get hourly sales for peak detection
    cur.execute("""
        SELECT DATE_PART('hour', actual_time) as hour,
               COUNT(*) as cups,
               AVG(ingredient_id) as top_item
        FROM sales_actuals
        WHERE shop_id = %s AND actual_time > NOW() - INTERVAL '7 days'
        GROUP BY hour
        ORDER BY cups DESC
    """, (shop_id,))
    
    # ... parse results into BusinessInsight
```

---

## API Reference

### GET /api/v1/business/insights/{shop_id}

**Response:**
```json
{
  "shop_id": "00000000-0000-0000-0000-000000000001",
  "generated_at": "2024-06-25T14:30:00Z",
  "peak_windows": [...],
  "today_revenue_estimate": 1200,
  "waste_percentage": 12.3,
  "top_drinks": [...],
  "inventory_optimizations": [...],
  "staff_efficiency_score": 87.5,
  "demo_mode": true
}
```

### GET /api/v1/business/revenue-forecast/{shop_id}

**Response:**
```json
{
  "shop_id": "00000000-0000-0000-0000-000000000001",
  "date": "2024-06-25",
  "current_revenue": 420,
  "current_hour": 14,
  "hours_remaining": 7,
  "avg_revenue_per_hour": 60,
  "projected_total_revenue": 840,
  "confidence": 0.85
}
```

### GET /api/v1/business/peak-windows/{shop_id}

**Response:**
```json
{
  "shop_id": "00000000-0000-0000-0000-000000000001",
  "peak_windows": [
    {
      "start_hour": 11,
      "end_hour": 13,
      "avg_cups_per_minute": 12.5,
      "confidence": 0.92,
      "label": "11:00 - 13:00"
    }
  ],
  "generated_at": "2024-06-25T14:30:00Z"
}
```

---

## Demo Mode vs. Real Data

### Demo Mode (Current)
- Uses synthetic but realistic data
- Generates peak windows: 11am-1pm (school rush), 5pm-7pm (after-work)
- Shows trending drinks and recommendations
- Perfect for testing UI and workflows

### Real Data Mode (Future Implementation)
- Queries PostgreSQL historical sales
- Analyzes actual transaction logs
- Computes real MAPE and waste percentages
- Machine learning insights from patterns

**Transition is transparent** — same API, no code changes needed in frontend.

---

## Business Impact

### Waste Reduction
- Current: ~12-15% waste (typical for manual management)
- Target: 8-10% waste with AI-driven prep
- **Savings:** 4-7% of daily ingredient cost

### Revenue Optimization
- Avoid stockouts during peak → no lost sales
- Trending drink detection → upselling opportunities
- Demand forecasting → optimized staffing

### Time Savings
- Staff don't guess when to prep
- Specific recommendations replace lengthy meetings
- 5 min/day reading insights vs. 30 min manual planning

---

## Future Enhancements

1. **Real Database Integration** — Replace synthetic with actual sales data
2. **ML Models** — LightGBM for demand forecasting instead of linear regression
3. **Anomaly Detection** — Alert if waste spikes unexpectedly
4. **Competitor Analysis** — If external data available
5. **Staff Performance Analytics** — Individual staff efficiency scores
6. **Promotions Engine** — Suggest discounts for slow-moving drinks
7. **Supplier Integration** — Auto-order when stock low

---

## Technical Details

### Data Model (Pydantic V2)

```python
class BusinessInsight(BaseModel):
    shop_id: UUID
    generated_at: datetime
    peak_windows: list[PeakWindow]
    today_revenue_estimate: float
    waste_percentage: float
    top_drinks: list[DrinkInsight]
    inventory_optimizations: list[InventoryOptimization]
    staff_efficiency_score: float
    demo_mode: bool
```

### Frontend State
```typescript
const [insights, setInsights] = useState<BusinessInsight | null>(null);
const [loading, setLoading] = useState(false);
const [revenue, setRevenue] = useState<any>(null);

// Refreshes every 5 minutes
useEffect(() => {
    fetchInsights();
    const interval = setInterval(fetchInsights, 5 * 60 * 1000);
    return () => clearInterval(interval);
}, []);
```

---

## Summary

Business Intelligence transforms BobaMaster from a **reactive system** (alert on problems) to a **proactive system** (prevent problems before they happen).

Staff see not just "what's happening now" but "what will happen in 2 hours and what to do about it."

**Result: Better decisions, happier customers, higher profits, less waste.**

