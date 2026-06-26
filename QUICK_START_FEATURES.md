# Quick Start — New Business Intelligence Features

## 🎉 What's New

BobaMaster now has a powerful **Business Intelligence Dashboard** that shows:
- Revenue forecasts
- Peak demand windows
- Top-selling drinks
- Inventory optimization tips
- Staff efficiency scores

---

## 🚀 How to Access

### 1. Start the Application
```bash
# Terminal 1 — Infrastructure
cd docker && docker-compose up -d

# Terminal 2 — Backend
cd backend && python app/database/init_db.py && uvicorn app.main:app --reload

# Terminal 3 — Frontend
cd frontend && npm run dev
```

### 2. Open Browser
```
http://localhost:5173
```

### 3. Navigate to Business Intelligence
- Look at the left sidebar navigation
- Click on the **Lightbulb icon** (or "Insights" text)
- You'll see the premium Business Intelligence dashboard

---

## 📊 Dashboard Tour

### Top Section: Key Metrics
Four colorful cards showing:
- **Green Card** — Today's Revenue ($XXX estimated)
- **Orange Card** — Waste Level (12.3%)
- **Blue Card** — Staff Efficiency (87.5%)
- **Purple Card** — Optimization Score (75%)

### Middle Left: Peak Demand Windows
A bar chart showing:
- When customers are busiest (usually 11am-1pm and 5pm-7pm)
- Heights of bars = how busy each hour is
- Use this to plan prep timing

### Middle Right: Top-Selling Drinks
A ranked table showing:
- #1 Most popular drink today
- #2 Second most popular
- Trend indicators (↑ up, ↓ down, → stable)
- Revenue for each drink

### Bottom: Optimization Recommendations
Cards with specific actions like:
- "Prepare 1.3kg more tapioca pearls by 4:30 PM to avoid shortage during evening rush"
- "Brown Sugar Pearl Milk trending up — increase inventory prep"
- Estimated impact (e.g., "Save 150g waste daily")

---

## 💡 Real Examples

### Scenario 1: Morning Shift (9 AM)
```
You arrive at the shop. Open BobaMaster:

Peak Windows shows: 11:00-13:00 rush at 12.5 cups/min
Optimization says: "Prepare extra tapioca pearls now (reach 2500g)"
Top Drinks shows: Classic Milk Tea trending up

Action: Start cooking pearls at 10:30 AM instead of 11:15 AM
Result: No stockout during rush, happy customers
```

### Scenario 2: Mid-Shift Decision (2 PM)
```
You check insights at 2 PM:

Revenue Forecast: On track for $840 today (up from $720 yesterday)
Waste Level: 12.3% (good, trending down)
Optimization shows: Matcha powder trending, current stock at 450g

Action: Cook 150g more matcha to have 600g by 5 PM
Result: Ready for after-work rush, capture trending demand
```

### Scenario 3: End of Day (8 PM)
```
Before closing, you review:

Today's Insights show:
- Revenue: $835 (forecast was $840 - very accurate!)
- Staff Efficiency: 89% (up from 87% yesterday!)
- Waste: 11.2% (down from yesterday's 12.3%)
- Top Drink: Classic Milk Tea (123 cups)

Action: Order more Classic Milk Tea supplies, plan for tomorrow's rush
Result: Data-driven decisions based on facts, not guesses
```

---

## 🎨 UI Features to Notice

### Color Coding
- **Green** — Good, healthy, proceed
- **Orange** — Warning, pay attention
- **Red** — Critical, take action now
- **Blue** — Information, forecast
- **Purple** — Analytics, insights

### Ingredient Status Cards (Main Dashboard)
Each ingredient shows:
- A **colored circle** (progress ring) with percentage
- A **top colored bar** indicating urgency
- Status label (Critical/Low/Healthy)
- Expiry time
- What's currently brewing

### Quick Actions (Dashboard)
Large, colorful buttons with:
- Icon
- Action name
- Brief description
- Click to jump to that section

### Charts
- **Peak Windows** — Bar chart showing demand by hour
- Heights represent intensity
- Opacity shows confidence (brighter = more confident)

---

## 📱 Responsive Design

### Mobile (Portrait)
- Single column
- Large buttons for easy tapping
- Stacked cards

### Tablet (Landscape)
- 2 columns
- Reasonable spacing
- Full visibility

### Desktop
- 3-4 columns
- Premium styling with shadows
- Full interactive experience

---

## 🔗 API Reference (Advanced)

If you want to call the API directly:

### Get Complete Insights
```bash
curl http://localhost:8000/api/v1/business/insights/00000000-0000-0000-0000-000000000001
```

Response includes:
- Peak demand windows
- Revenue estimate
- Top drinks with trends
- Inventory recommendations
- Staff efficiency score

### Get Revenue Forecast
```bash
curl http://localhost:8000/api/v1/business/revenue-forecast/00000000-0000-0000-0000-000000000001
```

Response includes:
- Current revenue
- Current hour
- Hours remaining
- Average per hour
- Projected total
- Confidence level

### Get Peak Windows
```bash
curl http://localhost:8000/api/v1/business/peak-windows/00000000-0000-0000-0000-000000000001
```

Response includes:
- Start/end hour for each peak
- Average cups per minute
- Confidence scores

---

## 📚 Full Documentation

For more details:
- `BUSINESS_INTELLIGENCE.md` — Complete feature guide
- `ENHANCEMENTS_SUMMARY.md` — Technical details and architecture
- `README.md` — Overall project documentation
- `DEPLOYMENT.md` — How to run and deploy

---

## ⚡ Tips & Tricks

### Make Better Decisions
1. **Check peak windows** — Know when to prep
2. **Read optimization cards** — Don't guess, follow data
3. **Watch the trends** — Spot changing customer preferences
4. **Track efficiency** — See if your team is improving

### Reduce Waste
- Follow specific inventory recommendations
- Prep only what forecasts say you'll need
- Act on trending drinks before waste happens

### Boost Revenue
- Start cooking BEFORE rush (don't run out)
- Notice trending drinks and upsell
- Use revenue forecast for staffing decisions

### Save Time
- 5 minutes reading insights vs. 30 minutes of guessing
- Clear recommendations vs. ambiguous meetings
- Same methodology for all staff (consistent)

---

## 🆘 Troubleshooting

### Dashboard shows "Demo data"
- This is normal and good
- Means synthetic data is being used (PostgreSQL not connected)
- Switch to real data later by updating the backend queries
- UI works identically either way

### Numbers look unrealistic
- Check timezone (timestamps in UTC)
- Check if it's the first time running (warm up data)
- Try refreshing or waiting 5 minutes for update

### Can't find the insights page
- Look for the **Lightbulb icon** in left sidebar
- If not visible, click "Insights" text
- Or use keyboard shortcut (if configured)

### Want to see updated data
- Click **"Refresh Insights"** button at bottom
- Auto-refreshes every 5 minutes anyway
- Data updates in real-time from backend

---

## 🎯 Next Steps

1. **Try it out** — Open insights page and explore
2. **Read the recommendations** — Follow specific actions
3. **Track results** — Did waste go down? Did revenue go up?
4. **Give feedback** — What would make it better?
5. **Share insights** — Show team the data-driven approach

---

## 📞 Questions?

- Check `BUSINESS_INTELLIGENCE.md` for detailed explanations
- Check `README.md` for architecture overview  
- Check `DEPLOYMENT.md` for setup and troubleshooting
- API docs at http://localhost:8000/docs (when backend running)

---

**Happy bubbling! 🧋 Let data guide your decisions.**

