"""End-to-End Demonstration of the Algorithmic Trading Backtester Data & Persistence Layer.

Demonstrates:
1. Database schema initialization & seeding
2. Instrument query with data range bounds
3. Price series extraction for strategy computation
4. Strategy creation with parameters
5. Atomic backtest run, trades, and performance metrics persistence
6. API-compatible JSON result extraction
"""
import json
from pprint import pprint
from datetime import date

from backend.persistence.database import engine, Base, SessionLocal
from backend.persistence.repositories import (
    UserRepo,
    InstrumentRepo,
    PriceRepo,
    StrategyRepo,
    BacktestRepo,
)
from backend.data_ingestion.seed import seed_database


def run_demo():
    print("=" * 60)
    print("ALGORITHMIC TRADING STRATEGY BACKTESTER - DATA LAYER DEMO")
    print("=" * 60)

    # 1. Run seed script
    print("\n[Step 1] Initializing schema and seeding instruments & prices...")
    seed_database()

    session = SessionLocal()
    try:
        user_repo = UserRepo(session=session)
        inst_repo = InstrumentRepo(session=session)
        price_repo = PriceRepo(session=session)
        strategy_repo = StrategyRepo(session=session)
        backtest_repo = BacktestRepo(session=session)

        # 2. Query instruments (with data bounds)
        print("\n[Step 2] Listing instruments with historical date ranges:")
        instruments = inst_repo.list_instruments()
        for inst in instruments:
            print(f"  - {inst['symbol']} ({inst['name']}) [{inst['exchange']}] "
                  f"Sector: {inst['sector']} | Data: {inst['data_start']} to {inst['data_end']}")

        aapl = next(i for i in instruments if i["symbol"] == "AAPL")

        # 3. Fetch price series for Strategy Engine (Member A)
        print(f"\n[Step 3] Fetching AAPL prices from {aapl['data_start']} to {aapl['data_end']}:")
        prices = price_repo.get_prices(
            instrument_id=aapl["id"],
            start_date=aapl["data_start"],
            end_date=aapl["data_end"],
        )
        print(f"  Fetched {len(prices)} bars sorted ascending by date.")
        print(f"  First bar: {prices[0]}")
        print(f"  Last bar:  {prices[-1]}")

        # 4. Fetch or create strategy
        user = user_repo.get_by_username("algo_trader")
        strategies = strategy_repo.list_strategies(user.id)
        selected_strategy = strategies[0]
        print(f"\n[Step 4] Using strategy: '{selected_strategy['name']}' (ID: {selected_strategy['id']})")
        print(f"  Parameters: {selected_strategy['parameters']}")

        # 5. Save backtest run (Member B & Member C integration)
        print("\n[Step 5] Simulating backtest execution and saving run atomically...")
        trades_payload = [
            {
                "entry_date": "2023-01-05",
                "entry_price": 144.64,
                "exit_date": "2023-01-13",
                "exit_price": 146.26,
                "quantity": 100.0,
                "pnl": 162.00,
            },
            {
                "entry_date": "2023-01-18",
                "entry_price": 146.00,
                "exit_date": "2023-01-25",
                "exit_price": 150.50,
                "quantity": 100.0,
                "pnl": 450.00,
            },
        ]

        metrics_payload = {
            "total_return": 0.0612,   # 6.12%
            "cagr": 0.185,            # 18.5%
            "sharpe_ratio": 1.74,
            "max_drawdown": -0.021,   # -2.1% (negative decimal)
            "win_rate": 1.0,          # 100% win rate
            "num_trades": 2,
        }

        run_id = backtest_repo.save_run(
            user_id=user.id,
            strategy_id=selected_strategy["id"],
            instrument_id=aapl["id"],
            start_date="2023-01-03",
            end_date="2023-02-06",
            initial_capital=10000.0,
            trades=trades_payload,
            metrics=metrics_payload,
            status="completed",
        )
        session.commit()
        print(f"  Backtest run saved successfully with run_id: {run_id}")

        # 6. Retrieve run matching API result object
        print(f"\n[Step 6] Retrieving run object (Contract for Member C's FastAPI / frontend):")
        run_result = backtest_repo.get_run(run_id)
        pprint(run_result)

        print("\n" + "=" * 60)
        print("DEMO RUN FINISHED SUCCESSFULLY!")
        print("=" * 60)

    finally:
        session.close()


if __name__ == "__main__":
    run_demo()
