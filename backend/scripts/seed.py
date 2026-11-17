"""
scripts/seed.py
Database seeding script. Seeds default users (including demo accounts for UI),
instruments from backend/data/*.csv, continuous historical price data across 2023,
sample strategies, and executed sample backtest runs.

Run via: python scripts/seed.py
"""
import os
import sys
import glob
import math
import random
from datetime import date, datetime, timedelta
from pathlib import Path
import pandas as pd

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import SessionLocal, engine
from app.core.security import hash_password
from app.models import Base, Instrument, PriceData, User, Strategy
from app.repositories.backtest_run_repository import BacktestRunRepository
from app.repositories.instrument_repository import InstrumentRepository
from app.repositories.metrics_repository import MetricsRepository
from app.repositories.strategy_repository import StrategyRepository
from app.services.backtest_engine import BacktestEngine
from app.services.metrics_calculator import MetricsCalculator

INSTRUMENTS_METADATA = [
    {"ticker": "AAPL", "name": "Apple Inc.", "asset_class": "EQUITY"},
    {"ticker": "MSFT", "name": "Microsoft Corp.", "asset_class": "EQUITY"},
    {"ticker": "GOOGL", "name": "Alphabet Inc.", "asset_class": "EQUITY"},
    {"ticker": "AMZN", "name": "Amazon.com Inc.", "asset_class": "EQUITY"},
    {"ticker": "TSLA", "name": "Tesla Inc.", "asset_class": "EQUITY"},
    {"ticker": "NVDA", "name": "NVIDIA Corp.", "asset_class": "EQUITY"},
    {"ticker": "META", "name": "Meta Platforms Inc.", "asset_class": "EQUITY"},
]


def seed() -> None:
    print("[Seed] Initializing database tables...")
    Base.metadata.create_all(engine)
    session = SessionLocal()

    try:
        # 1. Seed Users
        users_to_seed = [
            ("trader@jss.ac.in", "password123", "TRADER", "Trader Demo"),
            ("admin@jss.ac.in", "adminpass123", "ADMIN", "Admin Demo"),
            ("trader@example.com", "Trader@12345", "TRADER", "Demo Trader"),
            ("admin@example.com", "Admin@12345", "ADMIN", "Admin User"),
        ]

        user_objects = {}
        for email, pwd, role, name in users_to_seed:
            u = session.query(User).filter_by(email=email).first()
            if not u:
                u = User(
                    name=name,
                    email=email,
                    password_hash=hash_password(pwd),
                    role=role,
                )
                session.add(u)
                session.flush()
                print(f"[Seed] Created user: {email} ({role})")
            else:
                # Update password hash to guarantee match
                u.password_hash = hash_password(pwd)
                u.name = name
                session.flush()
            user_objects[email] = u

        # 2. Seed Instruments and Price Data from CSVs
        backend_dir = Path(__file__).resolve().parent.parent
        data_dir = backend_dir / "data"

        instrument_objects = {}
        for item in INSTRUMENTS_METADATA:
            ticker = item["ticker"]
            inst = session.query(Instrument).filter_by(ticker=ticker).first()
            if not inst:
                inst = Instrument(
                    ticker=ticker,
                    name=item["name"],
                    asset_class=item["asset_class"],
                )
                session.add(inst)
                session.flush()
                print(f"[Seed] Created instrument: {ticker} ({item['name']})")
            instrument_objects[ticker] = inst

            # Load CSV price data
            csv_path = data_dir / f"{ticker}.csv"
            existing_dates = {
                p.date
                for p in session.query(PriceData.date)
                .filter_by(instrument_id=inst.instrument_id)
                .all()
            }

            last_date = None
            last_close = 150.0

            if csv_path.exists():
                df = pd.read_csv(csv_path)
                # Normalize column headers
                cols = {c.strip().lower(): c for c in df.columns}
                for _, row in df.iterrows():
                    d_val = pd.to_datetime(row[cols["date"]]).date()
                    if d_val not in existing_dates:
                        p = PriceData(
                            instrument_id=inst.instrument_id,
                            date=d_val,
                            open=float(row[cols["open"]]),
                            high=float(row[cols["high"]]),
                            low=float(row[cols["low"]]),
                            close=float(row[cols["close"]]),
                            volume=float(row[cols["volume"]]),
                        )
                        session.add(p)
                        existing_dates.add(d_val)
                    last_date = d_val
                    last_close = float(row[cols["close"]])

            # If we have data up to Feb 6, extend forward through 2023-12-29
            # so the full 2023 calendar year has continuous weekday trading bars
            target_end_date = date(2023, 12, 29)
            if last_date is None:
                last_date = date(2023, 1, 2)

            cur_date = last_date + timedelta(days=1)
            rng = random.Random(hash(ticker) & 0xFFFFFFFF)

            while cur_date <= target_end_date:
                if cur_date.weekday() < 5 and cur_date not in existing_dates:
                    # Deterministic realistic daily price walk
                    pct_change = rng.uniform(-0.025, 0.026)
                    open_p = round(last_close * (1 + rng.uniform(-0.005, 0.005)), 2)
                    close_p = round(open_p * (1 + pct_change), 2)
                    high_p = round(max(open_p, close_p) * (1 + rng.uniform(0.001, 0.012)), 2)
                    low_p = round(min(open_p, close_p) * (1 - rng.uniform(0.001, 0.012)), 2)
                    vol = round(rng.uniform(12000000, 35000000), 0)

                    p = PriceData(
                        instrument_id=inst.instrument_id,
                        date=cur_date,
                        open=open_p,
                        high=high_p,
                        low=low_p,
                        close=close_p,
                        volume=vol,
                    )
                    session.add(p)
                    existing_dates.add(cur_date)
                    last_close = close_p
                cur_date += timedelta(days=1)

            session.flush()
            total_bars = (
                session.query(PriceData)
                .filter_by(instrument_id=inst.instrument_id)
                .count()
            )
            print(f"[Seed] {ticker}: {total_bars} price bars loaded.")

        # 3. Seed Strategies for Traders
        traders = [user_objects["trader@jss.ac.in"], user_objects["trader@example.com"]]
        seeded_strategies = []

        for trader in traders:
            strat1 = (
                session.query(Strategy)
                .filter_by(user_id=trader.user_id, strategy_type="MOVING_AVERAGE_CROSSOVER")
                .first()
            )
            if not strat1:
                strat1 = Strategy(
                    user_id=trader.user_id,
                    strategy_type="MOVING_AVERAGE_CROSSOVER",
                    parameters={"short_window": 5, "long_window": 20},
                )
                session.add(strat1)
                session.flush()
                print(f"[Seed] Created SMA 5/20 strategy for {trader.email}")
            seeded_strategies.append(strat1)

            strat2 = (
                session.query(Strategy)
                .filter_by(user_id=trader.user_id, strategy_type="MEAN_REVERSION")
                .first()
            )
            if not strat2:
                strat2 = Strategy(
                    user_id=trader.user_id,
                    strategy_type="MEAN_REVERSION",
                    parameters={"lookback_period": 20, "threshold": 1.5},
                )
                session.add(strat2)
                session.flush()
                print(f"[Seed] Created Mean Reversion strategy for {trader.email}")

        session.commit()

        # 4. Seed sample completed backtest runs
        jss_trader = user_objects["trader@jss.ac.in"]
        aapl_inst = instrument_objects["AAPL"]
        msft_inst = instrument_objects["MSFT"]

        jss_strategies = (
            session.query(Strategy).filter_by(user_id=jss_trader.user_id).all()
        )

        engine_svc = BacktestEngine(
            session=session,
            strategy_repo=StrategyRepository(session),
            instrument_repo=InstrumentRepository(session),
            run_repo=BacktestRunRepository(session),
            metrics_repo=MetricsRepository(session),
            calculator=MetricsCalculator(),
        )

        run_repo = BacktestRunRepository(session)
        existing_runs = run_repo.find_by_user(jss_trader.user_id)

        if not existing_runs and jss_strategies:
            print("[Seed] Running initial demo backtests for trader@jss.ac.in...")
            # Run 1: AAPL SMA Crossover
            run_id1 = engine_svc.run_backtest(
                user_id=jss_trader.user_id,
                strategy_id=jss_strategies[0].strategy_id,
                instrument_id=aapl_inst.instrument_id,
                start_date=date(2023, 1, 3),
                end_date=date(2023, 12, 29),
            )
            print(f"[Seed] Completed initial run 1 (AAPL SMA Crossover): ID #{run_id1}")

            # Run 2: MSFT if second strategy exists
            if len(jss_strategies) > 1:
                run_id2 = engine_svc.run_backtest(
                    user_id=jss_trader.user_id,
                    strategy_id=jss_strategies[1].strategy_id,
                    instrument_id=msft_inst.instrument_id,
                    start_date=date(2023, 1, 3),
                    end_date=date(2023, 12, 29),
                )
                print(f"[Seed] Completed initial run 2 (MSFT Mean Reversion): ID #{run_id2}")

        session.commit()
        print("\n==============================================")
        print("DATABASE SEEDING COMPLETED SUCCESSFULLY!")
        print("Accounts Available:")
        print("  - Trader: trader@jss.ac.in / password123")
        print("  - Admin:  admin@jss.ac.in  / adminpass123")
        print("  - Trader: trader@example.com / Trader@12345")
        print("  - Admin:  admin@example.com  / Admin@12345")
        print(f"Instruments Seeded: {', '.join(instrument_objects.keys())}")
        print("==============================================\n")

    except Exception as exc:
        session.rollback()
        print(f"[Seed] Error seeding database: {exc}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    seed()
