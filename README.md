# Algorithmic Trading Strategy Backtester — Data & Persistence Layer

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/release/python-3110/)
[![SQLAlchemy 2.x](https://img.shields.io/badge/SQLAlchemy-2.x-red.svg)](https://www.sqlalchemy.org/)
[![Alembic](https://img.shields.io/badge/Alembic-migrations-orange.svg)](https://alembic.sqlalchemy.org/)
[![Pytest](https://img.shields.io/badge/pytest-passing-brightgreen.svg)](https://pytest.org/)

This repository implements the **Data Ingestion, Database Schema, Persistence Layer, and Data Testing** for the 4-person Algorithmic Trading Strategy Backtester project.

---

## Architecture & Integration Contract

```mermaid
flowchart TD
    subgraph Data Layer ["Data & Persistence Layer (Our Scope)"]
        CSV["Yahoo Finance CSVs\n(data/*.csv)"] --> Loader["data_ingestion/loader.py\n(Validator & Gap Detector)"]
        Loader --> Repos["Repositories\n(User, Instrument, Price, Strategy, Backtest)"]
        Repos --> DB[(Relational DB\nSQLite / PostgreSQL)]
    end

    subgraph Teammate Integrations ["Team Integration Points"]
        SE["Member A: Strategy Engine"] -->|"PriceRepo.get_prices(...)"| Repos
        ME["Member B: Metrics Engine"] -->|"BacktestRepo.save_run(..., trades, metrics)"| Repos
        API["Member C: FastAPI / Web API"] -->|"UserRepo, InstrumentRepo,\nStrategyRepo, BacktestRepo"| Repos
    end
```

---

## 3NF Database Schema

```mermaid
erDiagram
    user ||--o{ strategy : "creates"
    user ||--o{ backtest_run : "launches"
    strategy ||--o{ strategy_parameter : "contains"
    strategy ||--o{ backtest_run : "executes"
    instrument ||--o{ price_data : "has"
    instrument ||--o{ backtest_run : "target"
    backtest_run ||--o{ trade : "records"
    backtest_run ||--|| performance_metric : "evaluates"

    user {
        int id PK
        string username UK
        string email UK
        string password_hash
        string role "trader | admin"
        datetime created_at
    }

    instrument {
        int id PK
        string symbol UK
        string name
        string exchange
        string sector
    }

    price_data {
        int id PK
        int instrument_id FK
        date date UK
        float open "CHECK > 0"
        float high "CHECK >= low"
        float low "CHECK > 0"
        float close "CHECK > 0"
        bigint volume "CHECK >= 0"
    }

    strategy {
        int id PK
        int user_id FK
        string name
        string type "moving_average_crossover | mean_reversion"
        datetime created_at
    }

    strategy_parameter {
        int id PK
        int strategy_id FK
        string param_name UK
        string param_value
    }

    backtest_run {
        int id PK
        int user_id FK
        int strategy_id FK
        int instrument_id FK
        date start_date
        date end_date "CHECK end_date > start_date"
        float initial_capital "CHECK > 0"
        string status "completed | failed"
        datetime created_at
    }

    trade {
        int id PK
        int run_id FK
        date entry_date
        float entry_price "CHECK > 0"
        date exit_date "CHECK exit_date >= entry_date"
        float exit_price "CHECK > 0"
        float quantity "CHECK > 0"
        float pnl
    }

    performance_metric {
        int id PK
        int run_id FK, UK
        float total_return
        float cagr
        float sharpe_ratio
        float max_drawdown "CHECK <= 0.0"
        float win_rate "CHECK 0.0 <= win_rate <= 1.0"
        int num_trades "CHECK >= 0"
    }
```

---

## Quick Start

### 1. Installation
```powershell
pip install -r requirements.txt
```

### 2. Run Database Migrations
```powershell
cd backend
python -m alembic upgrade head
```

### 3. Seed Instruments & Historical Price Data
```powershell
# From project root:
python -m backend.data_ingestion.seed
```

### 4. Run the Full Test Suite
```powershell
pytest backend/tests -v
```

### 5. Run the End-to-End Demo
```powershell
python demo.py
```

---

## Contract Rules & Conventions

- **Identifier Style**: `snake_case` everywhere. Database column names match the JSON field names used in API requests and responses.
- **Dates**: Python `datetime.date`, stored as `DATE` in SQL. Timestamps are timezone-aware UTC (`datetime.datetime(..., tzinfo=datetime.timezone.utc)`).
- **Ratios & Return Metrics**: Stored as decimals (`0.42` = 42%). `max_drawdown` is always negative or zero.
- **Null Safety**: Never returns `None` for metrics: if a run has zero trades, `num_trades=0`, `win_rate=0.0`, `sharpe_ratio=0.0`, `total_return=0.0`, `cagr=0.0`, and `max_drawdown=0.0`.
- **Database Engine Agnostic**: SQLite by default for development and testing (`PRAGMA foreign_keys=ON`). Works on PostgreSQL simply by setting `DATABASE_URL=postgresql+psycopg2://user:pass@host:5432/dbname`.

---

## Repository API Reference

All repositories return plain Python dictionaries (or standard types) rather than bound ORM objects, so the FastAPI and strategy layers require no internal database mechanics.

### `UserRepo`
```python
user = UserRepo.create_user(username="trader1", email="t1@backtester.io", password_hash="...", role="trader")
user = UserRepo.get_by_username("trader1")
```

### `InstrumentRepo`
```python
# Returns instruments including computed historical range bounds:
instruments = InstrumentRepo.list_instruments()
# [{"id": 1, "symbol": "AAPL", "name": "Apple Inc.", "exchange": "NASDAQ", "sector": "Technology", "data_start": date(2023, 1, 3), "data_end": date(2023, 2, 6)}]

inst = InstrumentRepo.get_instrument(1)
inst = InstrumentRepo.create_instrument(symbol="NVDA", name="NVIDIA Corp.", exchange="NASDAQ", sector="Technology")
InstrumentRepo.delete_instrument(1)  # Cascades to PriceData and BacktestRun
```

### `PriceRepo`
```python
# Sorted ASC by date; used directly by Member A's Strategy Engine
prices = PriceRepo.get_prices(instrument_id=1, start_date="2023-01-01", end_date="2023-02-01")
# [{"date": date(2023, 1, 3), "open": 150.0, "high": 151.25, "low": 145.3, "close": 146.4, "volume": 15000000}, ...]

rows_inserted = PriceRepo.bulk_insert_prices(instrument_id=1, rows=[...])
```

### `StrategyRepo`
```python
strategy = StrategyRepo.create_strategy(
    user_id=1,
    name="SMA 20/50 Crossover",
    type="moving_average_crossover",
    parameters={"fast_period": 20, "slow_period": 50}
)
strat = StrategyRepo.get_strategy(strategy["id"])
strategies = StrategyRepo.list_strategies(user_id=1)
updated = StrategyRepo.update_strategy(id=strategy["id"], parameters={"fast_period": 10})
StrategyRepo.delete_strategy(strategy["id"])
```

### `BacktestRepo`
```python
# Atomic transaction: saves run + trades + metrics in ONE transaction (rolls back fully on any error)
run_id = BacktestRepo.save_run(
    user_id=1,
    strategy_id=1,
    instrument_id=1,
    start_date="2023-01-03",
    end_date="2023-02-06",
    initial_capital=10000.0,
    trades=[
        {
            "entry_date": "2023-01-05",
            "entry_price": 144.64,
            "exit_date": "2023-01-13",
            "exit_price": 146.26,
            "quantity": 100.0,
            "pnl": 162.00
        }
    ],
    metrics={
        "total_return": 0.0612,
        "cagr": 0.185,
        "sharpe_ratio": 1.74,
        "max_drawdown": -0.021,
        "win_rate": 1.0,
        "num_trades": 1
    }
)

# Returns complete API result object with trades list and metrics dictionary:
run_dict = BacktestRepo.get_run(run_id)
runs = BacktestRepo.list_runs(user_id=1)
BacktestRepo.delete_run(run_id)  # Cascades to trades and performance_metric
```

---

## CSV Ingestion & Gap Detection

Yahoo Finance CSV files are loaded via `load_prices_from_csv(instrument_id, file_path)`.

**Return Schema (matching `POST /instruments/{id}/prices/upload`):**
```json
{
  "rows_loaded": 25,
  "rows_rejected": 0,
  "gaps_flagged": 1,
  "rejected_details": [
    { "row": 14, "reason": "high < low" }
  ],
  "gap_details": [
    { "from": "2022-03-01", "to": "2022-03-09" }
  ]
}
```

- **Gap Detection**: Any missing period longer than 4 consecutive calendar days between trading sessions is flagged without filling or crashing.
- **Idempotency**: Running ingestion on the same file multiple times yields the exact same database row count without error.
