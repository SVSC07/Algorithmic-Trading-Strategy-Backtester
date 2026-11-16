import os
import sys
from pathlib import Path
from typing import Dict, Any

from sqlalchemy import select

from backend.persistence.database import SessionLocal, engine, Base
from backend.persistence.models import Instrument, User, Strategy, StrategyParameter
from backend.persistence.repositories.user_repo import UserRepo
from backend.persistence.repositories.instrument_repo import InstrumentRepo
from backend.persistence.repositories.strategy_repo import StrategyRepo
from backend.data_ingestion.loader import load_prices_from_csv

INSTRUMENT_METADATA = {
    "AAPL": {"name": "Apple Inc.", "exchange": "NASDAQ", "sector": "Technology"},
    "MSFT": {"name": "Microsoft Corp.", "exchange": "NASDAQ", "sector": "Technology"},
    "GOOGL": {"name": "Alphabet Inc.", "exchange": "NASDAQ", "sector": "Communication Services"},
    "AMZN": {"name": "Amazon.com Inc.", "exchange": "NASDAQ", "sector": "Consumer Cyclical"},
    "TSLA": {"name": "Tesla Inc.", "exchange": "NASDAQ", "sector": "Consumer Cyclical"},
    "NVDA": {"name": "NVIDIA Corp.", "exchange": "NASDAQ", "sector": "Technology"},
    "META": {"name": "Meta Platforms Inc.", "exchange": "NASDAQ", "sector": "Communication Services"},
}


def find_data_dir() -> Path:
    """Find the data/ directory regardless of where script was invoked."""
    candidates = [
        Path(__file__).resolve().parent.parent / "data",
        Path.cwd() / "data",
        Path.cwd() / "backend" / "data",
    ]
    for p in candidates:
        if p.exists() and p.is_dir():
            return p
    raise FileNotFoundError("Could not locate data directory containing CSV files.")


def seed_database() -> Dict[str, Any]:
    """Seed instruments, demo user/strategies, and load historical price data."""
    # Ensure database schema tables exist
    Base.metadata.create_all(bind=engine)

    session = SessionLocal()
    results = {"instruments": [], "prices": {}}

    try:
        user_repo = UserRepo(session=session)
        instrument_repo = InstrumentRepo(session=session)
        strategy_repo = StrategyRepo(session=session)

        # 1. Seed demo user if not exists
        demo_user = user_repo.get_by_username("algo_trader")
        if not demo_user:
            demo_user = user_repo.create_user(
                username="algo_trader",
                email="trader@backtester.io",
                password_hash="$2b$12$eD82x4u9G4l0E4r...",
                role="trader",
            )
            print(f"[Seed] Created demo user: {demo_user.username}")

        # 2. Seed sample strategies
        existing_strategies = strategy_repo.list_strategies(demo_user.id)
        if not existing_strategies:
            strategy_repo.create_strategy(
                user_id=demo_user.id,
                name="SMA 20/50 Crossover",
                type="moving_average_crossover",
                parameters={"fast_period": 20, "slow_period": 50},
            )
            strategy_repo.create_strategy(
                user_id=demo_user.id,
                name="Bollinger Band Mean Reversion",
                type="mean_reversion",
                parameters={"window": 20, "std_dev": 2.0},
            )
            print("[Seed] Created default strategies")

        # 3. Seed instruments and price data from CSVs
        data_dir = find_data_dir()
        csv_files = sorted(list(data_dir.glob("*.csv")))
        print(f"[Seed] Found {len(csv_files)} CSV files in {data_dir}")

        for csv_path in csv_files:
            symbol = csv_path.stem.upper()
            meta = INSTRUMENT_METADATA.get(
                symbol,
                {"name": f"{symbol} Stock", "exchange": "US", "sector": "General"},
            )

            # Get or create instrument
            inst = session.execute(
                select(Instrument).where(Instrument.symbol == symbol)
            ).scalar_one_or_none()

            if not inst:
                inst = instrument_repo.create_instrument(
                    symbol=symbol,
                    name=meta["name"],
                    exchange=meta["exchange"],
                    sector=meta["sector"],
                )
                print(f"[Seed] Registered instrument: {inst.symbol}")
            else:
                print(f"[Seed] Instrument {inst.symbol} already exists")

            results["instruments"].append(inst.symbol)

            # Ingest price CSV
            ingest_result = load_prices_from_csv(
                instrument_id=inst.id,
                file_path=csv_path,
                session=session,
            )
            results["prices"][symbol] = ingest_result
            print(
                f"[Seed] {symbol}: loaded {ingest_result['rows_loaded']} rows, "
                f"rejected {ingest_result['rows_rejected']}, "
                f"gaps {ingest_result['gaps_flagged']}"
            )

        session.commit()
        print("[Seed] Seeding completed successfully.")
        return results

    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    seed_database()
