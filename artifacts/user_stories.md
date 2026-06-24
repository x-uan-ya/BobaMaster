# User Stories: Bobaflow Operations Platform

This document contains a catalog of 36 user stories detailing the functional expectations of the Bobaflow platform across eight distinct roles and stakeholders.

---

## 1. Store Manager Persona

*   **US-1.1:** As a Store Manager, I want to see a live visual indicator of remaining tapioca pearls and tea bases, so that I can monitor kitchen operations at a glance from my desk.
*   **US-1.2:** As a Store Manager, I want to receive an override notification when a recommendation is rejected by staff, so that I can investigate if the kitchen is falling behind or ignoring alerts.
*   **US-1.3:** As a Store Manager, I want to customize the safety buffer limits for peak hours, so that the AI increases the baseline warning threshold before high-traffic events.
*   **US-1.4:** As a Store Manager, I want to manually input known local events (e.g., a street fair next door), so that the AI can adjust its demand forecasting models for that day.
*   **US-1.5:** As a Store Manager, I want to see a weekly dashboard of cost losses due to discarded expired ingredients, so that I can track and report waste overhead to the business owner.
*   **US-1.6:** As a Store Manager, I want to receive a prompt to update the recipe book when new drinks are launched, so that the system correctly decomposes sales into raw ingredient deductions.

---

## 2. Shift Leader Persona

*   **US-2.1:** As a Shift Leader, I want the system to calculate the optimal prep times for secondary toppings (like pudding or grass jelly), so that they are ready before the afternoon rush.
*   **US-2.2:** As a Shift Leader, I want to see a list of active brewing countdowns on my console, so that I know which team member is cooking what batch and when it will finish.
*   **US-2.3:** As a Shift Leader, I want the system to alert me if pearls are nearing their 4-hour expiration mark, so that I can inspect their texture or authorize a promo deal to sell them off.
*   **US-2.4:** As a Shift Leader, I want to toggle a "busy kitchen mode" that adjusts alert intervals, so that my staff are not distracted by redundant alarms when short-staffed.
*   **US-2.5:** As a Shift Leader, I want to log mid-shift inventory recounts, so that I can reconcile discrepancies between POS estimated stock and actual physical stock.

---

## 3. Crew Member (Boba Chef) Persona

*   **US-3.1:** As a Crew Member, I want to hear a distinct audio tone when tapioca pearls need to be cooked, so that I don't have to constantly check the screen while washing cups.
*   **US-3.2:** As a Crew Member, I want a simple, one-tap "Start Cooking" button, so that I can quickly notify the system that I have started boiling a new batch.
*   **US-3.3:** As a Crew Member, I want a countdown timer displayed on a high-contrast screen in the kitchen, so that I know exactly when to simmer, rinse, and rest the pearls.
*   **US-3.4:** As a Crew Member, I want to log ingredient wastage (e.g. dropped a scoop of pearls) with a single-tap button, so that the AI's estimation of current stock remains accurate.
*   **US-3.5:** As a Crew Member, I want the screen to display a reminder checklist for brewing (e.g. water temperature, stir instructions), so that I maintain batch consistency.

---

## 4. Area Manager Persona

*   **US-4.1:** As an Area Manager, I want to compare the forecasting accuracy across all five stores under my jurisdiction, so that I can identify which stores need training on system usage.
*   **US-4.2:** As an Area Manager, I want to receive push notifications when any of my stores experience a critical stockout lasting longer than 15 minutes, so that I can intervene.
*   **US-4.3:** As an Area Manager, I want to see historical inventory loss comparisons, so that I can align ingredient margins across my entire region.
*   **US-4.4:** As an Area Manager, I want to sync staff schedules with prediction patterns, so that I can audit if managers are scheduling enough staff during high-forecast periods.
*   **US-4.5:** As an Area Manager, I want to benchmark pearl preparation waste percentages, so that I can define best-practice guidelines for my region.

---

## 5. Business Owner Persona

*   **US-5.1:** As a Business Owner, I want to see the system's net financial impact (cost of waste reduced vs. value of stockouts prevented), so that I can calculate the ROI of the software.
*   **US-5.2:** As a Business Owner, I want to receive a monthly executive summary of ingredient wastage, so that I can optimize supplier order contracts.
*   **US-5.3:** As a Business Owner, I want to audit how weather fluctuations correlate with my bottom line, so that I can plan seasonal marketing promotions.
*   **US-5.4:** As a Business Owner, I want to standardise recipes across my franchise network, so that every store calculates deductions and margins identically.
*   **US-5.5:** As a Business Owner, I want the system to flag supply-chain shortages based on localized crop reports (e.g. tapioca shortage), so that I can negotiate long-term pricing early.

---

## 6. Customer Persona

*   **US-6.1:** As a Customer ordering on the store mobile app, I want to be warned if tapioca pearls are temporarily out of stock before I complete checkout, so that I am not disappointed.
*   **US-6.2:** As a Customer, I want my bubble tea to always be served with fresh, chewy pearls, so that I get a high-quality product every time I visit.
*   **US-6.3:** As a Customer, I want my order wait time to be under 5 minutes during busy hours, so that I can grab my tea quickly on my way to work.
*   **US-6.4:** As a Customer, I want to see accurate stock levels for limited-edition seasonal tea bases on the menu board, so that I don't order something that is unavailable.

---

## 7. Delivery Rider Persona

*   **US-7.1:** As a Delivery Rider, I want the merchant's preparation timer on my app to update dynamically based on the kitchen's active pearl status, so that I don't waste time waiting at the store.
*   **US-7.2:** As a Delivery Rider, I want to know if an order contains ingredients currently being brewed, so that I can adjust my pickup route sequence to prioritize other deliveries first.
*   **US-7.3:** As a Delivery Rider, I want bubble tea containers to be ready exactly when I arrive, so that my courier ratings remain high and the drinks do not melt or get warm.

---

## 8. Other Franchisees / Bubble Tea Shop Owners Persona

*   **US-8.1:** As a fellow franchisee, I want to opt into sharing anonymous, aggregated sales velocity benchmarks, so that I can see if my store's performance is on par with city-wide averages.
*   **US-8.2:** As a neighboring franchisee, I want to share warnings about regional supply delays, so that we can coordinate emergency ingredient transfers (e.g. loaning 5 bags of pearls).
*   **US-8.3:** As a co-op franchisee member, I want to see joint purchasing forecasts for raw ingredients, so that we can pool our orders together to negotiate volume discounts from importers.
