# STUB, owned by Rishabh, replaced on merge
from datetime import date, timedelta
import random
from app.core.database import SessionLocal, engine
from app.models.base import Base
from app.models.user import User
from app.models.instrument import Instrument
from app.models.price_data import PriceData
from app.core.security import hash_password

def seed_database():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()

    try:
        # Seed Admin user
        admin = session.query(User).filter(User.email == "admin@example.com").first()
        if not admin:
            admin = User(
                name="Admin User",
                email="admin@example.com",
                password_hash=hash_password("admin12345"),
                role="ADMIN",
            )
            session.add(admin)

        # Seed Trader user
        trader = session.query(User).filter(User.email == "trader@example.com").first()
        if not trader:
            trader = User(
                name="Trader User",
                email="trader@example.com",
                password_hash=hash_password("trader12345"),
                role="TRADER",
            )
            session.add(trader)

        session.commit()

        # Seed Instruments
        instruments_data = [
            ("AAPL", "Apple Inc.", "Equity"),
            ("MSFT", "Microsoft Corporation", "Equity"),
            ("BTC-USD", "Bitcoin USD", "Crypto"),
        ]

        instruments = []
        for ticker, name, asset_class in instruments_data:
            inst = session.query(Instrument).filter(Instrument.ticker == ticker).first()
            if not inst:
                inst = Instrument(ticker=ticker, name=name, asset_class=asset_class)
                session.add(inst)
                session.flush()
            instruments.append(inst)

        session.commit()

        # Seed Price Data (past 120 days)
        base_date = date.today() - timedelta(days=120)
        random.seed(42)

        for inst in instruments:
            count = session.query(PriceData).filter(PriceData.instrument_id == inst.instrument_id).count()
            if count == 0:
                current_price = 150.0 if inst.ticker == "AAPL" else (300.0 if inst.ticker == "MSFT" else 60000.0)
                for day_offset in range(120):
                    curr_date = base_date + timedelta(days=day_offset)
                    # Skip weekends for equities
                    if inst.asset_class == "Equity" and curr_date.weekday() >= 5:
                        continue
                    change = (random.random() - 0.48) * (current_price * 0.02)
                    open_p = round(current_price, 2)
                    close_p = round(max(1.0, current_price + change), 2)
                    high_p = round(max(open_p, close_p) + random.random() * 2.0, 2)
                    low_p = round(min(open_p, close_p) - random.random() * 2.0, 2)
                    vol = round(random.randint(100000, 5000000), 0)
                    current_price = close_p

                    price_record = PriceData(
                        instrument_id=inst.instrument_id,
                        date=curr_date,
                        open=open_p,
                        high=high_p,
                        low=low_p,
                        close=close_p,
                        volume=vol,
                    )
                    session.add(price_record)

        session.commit()
        print("Database seeded successfully.")
    finally:
        session.close()

if __name__ == "__main__":
    seed_database()
