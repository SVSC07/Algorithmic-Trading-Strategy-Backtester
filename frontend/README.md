# QuantBacktest Pro — Frontend Application

> **Project:** Algorithmic Trading Strategy Backtester  
> **Course:** Software Engineering Mini Project, JSS University Noida  
> **Frontend Owner:** Shourya (UI/UX and Product Designer)  
> **Stack:** React 19, TypeScript, Vite, Recharts, Vitest  

---

## 1. Overview & Aesthetics

The frontend implements the **Presentation Layer (Figure 6)** of the system contract. The visual design is inspired by modern high-end fintech aesthetics, featuring:

* **Signature Color Palette:**
  * **Accent Lime:** `#A3E635` / `#A8F349` (used for active pill navigation, benchmark cards, and primary interactive highlights)
  * **Dark Forest Accent:** `#0F2617` (used for high-contrast primary actions and brand pill tags)
  * **Canvas Background:** `#EDEDED` (soft neutral clay/warm grey)
  * **Card Surfaces:** `#FFFFFF` (crisp white with `22px` rounded corners and subtle hairline borders)
  * **Financial Gains / Losses:** `#16A34A` for positive returns / PnL; `#DC2626` for losses / drawdowns
* **Design Principles:** Strict minimalism, tabular numerals for monetary data, zero decorative emojis (100% vector SVG icons via Lucide), micro-interactions on hover, and full WCAG AA contrast compliance.

---

## 2. Six System Views (Experiment 4)

1. **Authentication (`/login`) — FR-1:**
   * Unified Login and Register view with smooth toggle switch.
   * Redirects `TRADER` to `/run` and `ADMIN` to `/admin/instruments`.
   * Includes one-click demo credentials (`Trader Demo` and `Admin Demo`).
2. **Strategy Configuration (`/strategies`) — FR-2:**
   * Dynamic form for `MOVING_AVERAGE_CROSSOVER` (short/long windows) and `MEAN_REVERSION` (lookback period, threshold).
   * Real-time inline validation (e.g., ensuring `short_window < long_window`).
   * Clean one-line summary list of active algorithms (e.g., `Moving Average Crossover, 20 / 50`).
3. **Backtest Run View (`/run`) — FR-3 & FR-10:**
   * Strategy and Instrument selectors with dynamic historical date coverage display (`data_start` to `data_end`).
   * Explicit handling for `422 INSUFFICIENT_DATA` displaying the available date range.
   * Recent backtests summary table with return badges and direct links to execution results.
4. **Results View (`/results/:id`) — FR-5 & FR-6:**
   * Five key metric figures: Total Return, CAGR, Sharpe Ratio, Max Drawdown, Win Rate.
   * Recharts equity curve with filled dots (`●`) for Buy entries and hollow dots (`○`) for Sell exits.
   * Granular trade execution log table. Handles zero-trade runs displaying `"No trades were generated for this range."`
5. **Comparison View (`/compare`) — FR-7:**
   * Dual dropdown run selectors fed from recent backtest history.
   * Side-by-side metric comparison table with difference column ($\Delta A - B$).
   * Dual equity curve overlay chart with Run A in accent and Run B in muted tones.
6. **Instrument Administration (`/admin/instruments`) — FR-8:**
   * Protected administrative universe management.
   * Add new instruments, inline ticker/name/asset class editing, and delete with safety confirmation.
   * CSV EOD price series importer with report summary (imported bars, skipped bars, first 5 error diagnostics).

---

## 3. Getting Started

### Prerequisites
* **Node.js:** v18+ (tested on Node v25 / npm v11)
* **Backend:** (Optional) FastAPI backend on port 8000. When offline, mock mode runs seamlessly.

### Installation
```bash
cd frontend
npm install
```

### Running Locally

#### Mode A: Client-Side Mock Fixtures (Default)
Runs entirely standalone without requiring the backend server or PostgreSQL database:
```bash
npm run dev
```
Navigate to [http://localhost:5173](http://localhost:5173).

#### Mode B: Connecting to Real Backend API
When the backend branch is active on `http://localhost:8000`:
Create `.env.local` or run:
```bash
VITE_USE_MOCKS=false npm run dev
```
The API client connects directly to `http://localhost:8000` via bearer token authentication with zero component code changes.

---

## 4. Running Tests & Production Build

### Unit & Integration Tests (Vitest)
Executes tests covering format helpers, API error envelope parsing, strategy validation, and role-based route guards:
```bash
npm test
```

### Production Build
Verifies TypeScript compilation and creates the production bundle:
```bash
npm run build
```

---

## 5. Report Screenshots

Report screenshots for each of the six views are saved in `docs/screens/`:
* `01_login.png` — Login & Register view
* `02_run.png` — Backtest run setup & recent runs
* `03_strategies.png` — Parametric strategy configuration
* `04_results.png` — Results telemetry & equity curve
* `05_compare.png` — Side-by-side strategy comparison
* `06_admin_instruments.png` — Admin instrument registry
