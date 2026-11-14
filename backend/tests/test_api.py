"""
Integration tests for FastAPI endpoints and Error Envelopes.
Owned by Molik.
"""
from datetime import date, timedelta
from app.models.instrument import Instrument
from app.models.price_data import PriceData

def test_health_check(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}

def test_fastapi_validation_error_remapped_to_400(client):
    # Malformed JSON / missing fields must yield 400 VALIDATION_ERROR (not 422)
    res = client.post("/api/auth/login", json={"email": "not-an-email"})
    assert res.status_code == 400
    data = res.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"

def test_auth_routes(client):
    # Register trader
    res = client.post(
        "/api/auth/register",
        json={"name": "Trader Tom", "email": "tom@test.com", "password": "password123"},
    )
    assert res.status_code == 201
    body = res.json()
    assert body["role"] == "TRADER"
    assert "password" not in body

    # Duplicate register -> 409 CONFLICT
    res_dup = client.post(
        "/api/auth/register",
        json={"name": "Trader Tom", "email": "tom@test.com", "password": "password123"},
    )
    assert res_dup.status_code == 409
    assert res_dup.json()["error"]["code"] == "CONFLICT"

    # Login
    res_login = client.post(
        "/api/auth/login",
        json={"email": "tom@test.com", "password": "password123"},
    )
    assert res_login.status_code == 200
    assert "token" in res_login.json()

def test_strategies_api(client, seed_users):
    headers = {"Authorization": f"Bearer {seed_users['trader_token']}"}

    # Create strategy
    res = client.post(
        "/api/strategies",
        headers=headers,
        json={
            "strategy_type": "MOVING_AVERAGE_CROSSOVER",
            "parameters": {"short_window": 5, "long_window": 20},
        },
    )
    assert res.status_code == 201
    strat = res.json()
    assert strat["strategy_type"] == "MOVING_AVERAGE_CROSSOVER"

    # List strategies
    res_list = client.get("/api/strategies", headers=headers)
    assert res_list.status_code == 200
    items = res_list.json()
    assert len(items) == 1
    assert items[0]["strategy_id"] == strat["strategy_id"]

def test_instruments_api_admin_and_trader(client, seed_users):
    admin_h = {"Authorization": f"Bearer {seed_users['admin_token']}"}
    trader_h = {"Authorization": f"Bearer {seed_users['trader_token']}"}

    # Trader cannot create instrument -> 403 FORBIDDEN
    res_forbidden = client.post(
        "/api/instruments",
        headers=trader_h,
        json={"ticker": "TSLA", "name": "Tesla Inc.", "asset_class": "Equity"},
    )
    assert res_forbidden.status_code == 403

    # Admin creates instrument -> 201
    res_create = client.post(
        "/api/instruments",
        headers=admin_h,
        json={"ticker": "TSLA", "name": "Tesla Inc.", "asset_class": "Equity"},
    )
    assert res_create.status_code == 201
    inst_id = res_create.json()["instrument_id"]

    # Trader can list instruments -> 200
    res_list = client.get("/api/instruments", headers=trader_h)
    assert res_list.status_code == 200
    assert any(i["ticker"] == "TSLA" for i in res_list.json())

    # Admin delete instrument -> 204
    res_del = client.delete(f"/api/instruments/{inst_id}", headers=admin_h)
    assert res_del.status_code == 204

def test_backtest_execution_and_results_api(client, seed_users, db_session):
    trader_h = {"Authorization": f"Bearer {seed_users['trader_token']}"}

    # 1. Create strategy
    res_strat = client.post(
        "/api/strategies",
        headers=trader_h,
        json={
            "strategy_type": "MOVING_AVERAGE_CROSSOVER",
            "parameters": {"short_window": 2, "long_window": 4},
        },
    )
    strat_id = res_strat.json()["strategy_id"]

    # 2. Add instrument and prices
    inst = Instrument(ticker="SPY", name="S&P 500 ETF", asset_class="ETF")
    db_session.add(inst)
    db_session.commit()

    dates = [date(2024, 1, 1) + timedelta(days=i) for i in range(8)]
    closes = [10.0, 10.0, 10.0, 10.0, 14.0, 14.0, 6.0, 6.0]
    for d, c in zip(dates, closes):
        db_session.add(PriceData(instrument_id=inst.instrument_id, date=d, open=c, high=c+1, low=c-1, close=c, volume=1000))
    db_session.commit()

    # 3. Post backtest -> 201 COMPLETED
    res_bt = client.post(
        "/api/backtests",
        headers=trader_h,
        json={
            "strategy_id": strat_id,
            "instrument_id": inst.instrument_id,
            "start_date": "2024-01-01",
            "end_date": "2024-01-08",
        },
    )
    assert res_bt.status_code == 201
    run_id = res_bt.json()["run_id"]

    # 4. List backtests -> 200
    res_list = client.get("/api/backtests", headers=trader_h)
    assert res_list.status_code == 200
    assert len(res_list.json()) == 1

    # 5. Detail
    res_detail = client.get(f"/api/backtests/{run_id}", headers=trader_h)
    assert res_detail.status_code == 200
    detail = res_detail.json()
    assert detail["run"]["run_id"] == run_id
    assert "metrics" in detail
    assert "equity_curve" in detail

    # 6. Trades endpoint
    res_trades = client.get(f"/api/backtests/{run_id}/trades", headers=trader_h)
    assert res_trades.status_code == 200
    assert len(res_trades.json()) == 1

    # 7. Compare endpoint
    res_compare = client.get(f"/api/backtests/compare?runA={run_id}&runB={run_id}", headers=trader_h)
    assert res_compare.status_code == 200
    compare_data = res_compare.json()
    assert "run_a" in compare_data
    assert "run_b" in compare_data
