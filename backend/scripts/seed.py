# STUB, owned by Rishabh, replaced on merge
"""
scripts/seed.py
Database seeding script. Seeds default admin user, sample trader, and sample instrument.
Run via: python scripts/seed.py
"""
import os
import sys
from datetime import date, timedelta

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import SessionLocal, engine
from app.core.security import hash_password
from app.models import Base, Instrument, PriceData, User


def seed() -> None:
    Base.metadata.create_all(engine)
    session = SessionLocal()
    try:
        # Seed Admin user
        admin = session.query(User).filter_by(email="admin@example.com").first()
        if not admin:
            admin = User(
                name="Admin User",
                email="admin@example.com",
                password_hash=hash_password("Admin@12345"),
                role="ADMIN",
            )
            session.add(admin)

        # Seed Trader user
        trader = session.query(User).filter_by(email="trader@example.com").first()
        if not trader:
            trader = User(
                name="Demo Trader",
                email="trader@example.com",
                password_hash=hash_password("Trader@12345"),
                role="TRADER",
            )
            session.add(trader)

        # Seed sample Instrument: AAPL
        inst = session.query(Instrument).filter_by(ticker="AAPL").first()
        if not inst:
            inst = Instrument(
                ticker="AAPL",
                name="Apple Inc.",
                asset_class="EQUITY",
            )
            session.add(inst)
            session.flush()

            # Seed 100 days of price data
            cur_date = date(2023, 1, 2)
            base_price = 150.0
            count = 0
            while count < 100:
                if cur_date.weekday() < 5:
                    var = (count % 7) - 3.0
                    close = round(base_price + var, 2)
                    p = PriceData(
                        instrument_id=inst.instrument_id,
                        date=cur_date,
                        open=base_price,
                        high=close + 2.0,
                        low=base_price - 2.0,
                        close=close,
                        volume=50000.0,
                    )
                    session.add(p)
                    base_price = close
                    count += 1
                cur_date += timedelta(days=1)

        session.commit()
        print("Database seeded successfully.")
    except Exception as exc:
        session.rollback()
        print(f"Error seeding database: {exc}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    seed()
