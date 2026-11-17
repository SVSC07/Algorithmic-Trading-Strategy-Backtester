"""
tests/test_integration.py
Integration tests (Milestone 5) — full happy-path and failure-path flows.

Uses FastAPI TestClient with in-memory SQLite (no Postgres required).
Covers: register → login → create strategy → create instrument → import prices →
run backtest → get run detail → list runs → compare runs → reproducibility.
Failure paths: 400, 401, 403, 404, 409, 422.
"""
import io
import os

import pytest

os.environ.setdefault("SECRET_KEY", "integration-test-secret-key-at-least-32-bytes")

from tests.conftest import auth_header, make_price_csv


# ---------------------------------------------------------------------------
# Full happy-path flow
# ---------------------------------------------------------------------------

class TestHappyPath:
    def test_register_and_login(self, client):
        # Register
        r = client.post("/api/auth/register", json={
            "name": "Alice", "email": "alice@flow.com", "password": "password123",
        })
        assert r.status_code == 201
        body = r.json()
        assert body["role"] == "TRADER"
        assert body["email"] == "alice@flow.com"

        # Login
        r = client.post("/api/auth/login", json={
            "email": "alice@flow.com", "password": "password123",
        })
        assert r.status_code == 200
        assert "token" in r.json()
        assert r.json()["user"]["role"] == "TRADER"

    def test_full_backtest_flow(self, client, seeded_users):
        admin_token, trader_token, admin, trader = seeded_users

        # Admin creates instrument
        r = client.post("/api/instruments", json={
            "ticker": "AAPL", "name": "Apple Inc.", "asset_class": "EQUITY",
        }, headers=auth_header(admin_token))
        assert r.status_code == 201
        inst_id = r.json()["instrument_id"]

        # Admin imports prices
        csv_data = make_price_csv(n_days=60)
        r = client.post(
            f"/api/instruments/{inst_id}/prices",
            files={"file": ("prices.csv", io.BytesIO(csv_data), "text/csv")},
            headers=auth_header(admin_token),
        )
        assert r.status_code == 200
        assert r.json()["imported"] > 0

        # Trader creates strategy
        r = client.post("/api/strategies", json={
            "strategy_type": "MOVING_AVERAGE_CROSSOVER",
            "parameters": {"short_window": 5, "long_window": 20},
        }, headers=auth_header(trader_token))
        assert r.status_code == 201
        strat_id = r.json()["strategy_id"]

        # Trader runs backtest
        r = client.post("/api/backtests", json={
            "strategy_id": strat_id,
            "instrument_id": inst_id,
            "start_date": "2023-01-02",
            "end_date": "2023-03-31",
        }, headers=auth_header(trader_token))
        assert r.status_code == 201
        run_id = r.json()["run_id"]
        assert r.json()["status"] == "COMPLETED"

        # Get run detail
        r = client.get(f"/api/backtests/{run_id}", headers=auth_header(trader_token))
        assert r.status_code == 200
        detail = r.json()
        assert detail["run"]["run_id"] == run_id
        assert detail["metrics"] is not None
        assert "sharpe_ratio" in detail["metrics"]
        assert "equity_curve" in detail
        assert len(detail["equity_curve"]) > 0

        # Metrics row exists (all keys present)
        for k in ("sharpe_ratio", "max_drawdown", "win_rate", "cagr", "total_return"):
            assert k in detail["metrics"]

        # List runs — newest first
        r = client.get("/api/backtests", headers=auth_header(trader_token))
        assert r.status_code == 200
        summaries = r.json()
        assert len(summaries) >= 1
        assert summaries[0]["run_id"] == run_id

    def test_compare_two_runs(self, client, seeded_users):
        admin_token, trader_token, admin, trader = seeded_users

        # Setup instrument + prices
        r = client.post("/api/instruments", json={
            "ticker": "GOOG", "name": "Google", "asset_class": "EQUITY",
        }, headers=auth_header(admin_token))
        inst_id = r.json()["instrument_id"]
        csv_data = make_price_csv(n_days=60)
        client.post(
            f"/api/instruments/{inst_id}/prices",
            files={"file": ("p.csv", io.BytesIO(csv_data), "text/csv")},
            headers=auth_header(admin_token),
        )

        # Two strategies
        r1 = client.post("/api/strategies", json={
            "strategy_type": "MOVING_AVERAGE_CROSSOVER",
            "parameters": {"short_window": 5, "long_window": 20},
        }, headers=auth_header(trader_token))
        s1 = r1.json()["strategy_id"]

        r2 = client.post("/api/strategies", json={
            "strategy_type": "MEAN_REVERSION",
            "parameters": {"lookback_period": 10, "threshold": 1.5},
        }, headers=auth_header(trader_token))
        s2 = r2.json()["strategy_id"]

        # Two runs
        run1 = client.post("/api/backtests", json={
            "strategy_id": s1, "instrument_id": inst_id,
            "start_date": "2023-01-02", "end_date": "2023-03-31",
        }, headers=auth_header(trader_token)).json()["run_id"]

        run2 = client.post("/api/backtests", json={
            "strategy_id": s2, "instrument_id": inst_id,
            "start_date": "2023-01-02", "end_date": "2023-03-31",
        }, headers=auth_header(trader_token)).json()["run_id"]

        # Compare
        r = client.get(f"/api/backtests/compare?runA={run1}&runB={run2}",
                       headers=auth_header(trader_token))
        assert r.status_code == 200
        result = r.json()
        assert "run_a" in result and "run_b" in result
        assert result["run_a"]["run"]["run_id"] == run1
        assert result["run_b"]["run"]["run_id"] == run2

    def test_reproducibility(self, client, seeded_users):
        """Running the same inputs twice must yield identical metrics."""
        admin_token, trader_token, admin, trader = seeded_users

        r = client.post("/api/instruments", json={
            "ticker": "REPRO", "name": "ReproTest", "asset_class": "EQUITY",
        }, headers=auth_header(admin_token))
        inst_id = r.json()["instrument_id"]
        csv_data = make_price_csv(n_days=60)
        client.post(
            f"/api/instruments/{inst_id}/prices",
            files={"file": ("p.csv", io.BytesIO(csv_data), "text/csv")},
            headers=auth_header(admin_token),
        )

        r = client.post("/api/strategies", json={
            "strategy_type": "MOVING_AVERAGE_CROSSOVER",
            "parameters": {"short_window": 5, "long_window": 20},
        }, headers=auth_header(trader_token))
        strat_id = r.json()["strategy_id"]

        payload = {
            "strategy_id": strat_id, "instrument_id": inst_id,
            "start_date": "2023-01-02", "end_date": "2023-03-31",
        }

        run1 = client.post("/api/backtests", json=payload,
                           headers=auth_header(trader_token)).json()["run_id"]
        run2 = client.post("/api/backtests", json=payload,
                           headers=auth_header(trader_token)).json()["run_id"]

        m1 = client.get(f"/api/backtests/{run1}",
                        headers=auth_header(trader_token)).json()["metrics"]
        m2 = client.get(f"/api/backtests/{run2}",
                        headers=auth_header(trader_token)).json()["metrics"]
        assert m1 == m2, f"Metrics differ: {m1} vs {m2}"


# ---------------------------------------------------------------------------
# Failure paths
# ---------------------------------------------------------------------------

class TestAuthFailures:
    def test_no_token_returns_401(self, client):
        r = client.get("/api/strategies")
        assert r.status_code == 401
        assert r.json()["error"]["code"] == "UNAUTHENTICATED"

    def test_bad_token_returns_401(self, client):
        r = client.get("/api/strategies", headers={"Authorization": "Bearer garbage"})
        assert r.status_code == 401

    def test_trader_on_admin_route_returns_403(self, client, seeded_users):
        _, trader_token, _, _ = seeded_users
        r = client.post("/api/instruments", json={
            "ticker": "X", "name": "X", "asset_class": "EQUITY",
        }, headers=auth_header(trader_token))
        assert r.status_code == 403
        assert r.json()["error"]["code"] == "FORBIDDEN"

    def test_bad_body_returns_400(self, client):
        r = client.post("/api/auth/register", json={
            "name": "X", "email": "not-an-email", "password": "password123",
        })
        assert r.status_code == 400
        assert r.json()["error"]["code"] == "VALIDATION_ERROR"

    def test_start_date_gte_end_date_returns_400(self, client, seeded_users):
        _, trader_token, _, _ = seeded_users
        r = client.post("/api/backtests", json={
            "strategy_id": 1, "instrument_id": 1,
            "start_date": "2023-05-01", "end_date": "2023-01-01",
        }, headers=auth_header(trader_token))
        assert r.status_code == 400
        assert r.json()["error"]["code"] == "VALIDATION_ERROR"

    def test_equal_dates_returns_400(self, client, seeded_users):
        _, trader_token, _, _ = seeded_users
        r = client.post("/api/backtests", json={
            "strategy_id": 1, "instrument_id": 1,
            "start_date": "2023-01-01", "end_date": "2023-01-01",
        }, headers=auth_header(trader_token))
        assert r.status_code == 400
        assert r.json()["error"]["code"] == "VALIDATION_ERROR"


class TestConflictErrors:
    def test_duplicate_email_returns_409(self, client):
        client.post("/api/auth/register", json={
            "name": "Alice", "email": "dup@test.com", "password": "password123",
        })
        r = client.post("/api/auth/register", json={
            "name": "Alice2", "email": "dup@test.com", "password": "password456",
        })
        assert r.status_code == 409
        assert r.json()["error"]["code"] == "CONFLICT"

    def test_duplicate_ticker_returns_409(self, client, seeded_users):
        admin_token, _, _, _ = seeded_users
        client.post("/api/instruments", json={
            "ticker": "DUP", "name": "Dup", "asset_class": "EQUITY",
        }, headers=auth_header(admin_token))
        r = client.post("/api/instruments", json={
            "ticker": "DUP", "name": "Dup2", "asset_class": "EQUITY",
        }, headers=auth_header(admin_token))
        assert r.status_code == 409
        assert r.json()["error"]["code"] == "CONFLICT"

    def test_delete_instrument_in_use_returns_409(self, client, seeded_users):
        admin_token, trader_token, _, trader = seeded_users

        # Create instrument + prices
        r = client.post("/api/instruments", json={
            "ticker": "INUSE", "name": "InUse", "asset_class": "EQUITY",
        }, headers=auth_header(admin_token))
        inst_id = r.json()["instrument_id"]

        csv_data = make_price_csv(n_days=60)
        client.post(
            f"/api/instruments/{inst_id}/prices",
            files={"file": ("p.csv", io.BytesIO(csv_data), "text/csv")},
            headers=auth_header(admin_token),
        )

        # Create strategy and run backtest
        r = client.post("/api/strategies", json={
            "strategy_type": "MOVING_AVERAGE_CROSSOVER",
            "parameters": {"short_window": 5, "long_window": 20},
        }, headers=auth_header(trader_token))
        strat_id = r.json()["strategy_id"]

        client.post("/api/backtests", json={
            "strategy_id": strat_id, "instrument_id": inst_id,
            "start_date": "2023-01-02", "end_date": "2023-03-31",
        }, headers=auth_header(trader_token))

        # Try to delete — should be 409
        r = client.delete(f"/api/instruments/{inst_id}",
                          headers=auth_header(admin_token))
        assert r.status_code == 409
        assert r.json()["error"]["code"] == "CONFLICT"


class TestNotFoundErrors:
    def test_another_users_run_returns_404(self, client, seeded_users, db_session):
        admin_token, trader_token, admin, trader = seeded_users

        # Create a run for another user using a second trader
        from app.models import User as UserModel
        from app.core.security import hash_password, create_token
        u2 = UserModel(
            name="Eve", email="eve@test.com",
            password_hash=hash_password("evepassword1"),
            role="TRADER",
        )
        db_session.add(u2)
        db_session.commit()
        db_session.refresh(u2)
        eve_token = create_token(u2.user_id, "TRADER")

        # Setup instrument + prices as admin
        r = client.post("/api/instruments", json={
            "ticker": "EVE", "name": "Eve Corp", "asset_class": "EQUITY",
        }, headers=auth_header(admin_token))
        inst_id = r.json()["instrument_id"]
        csv_data = make_price_csv(n_days=60)
        client.post(
            f"/api/instruments/{inst_id}/prices",
            files={"file": ("p.csv", io.BytesIO(csv_data), "text/csv")},
            headers=auth_header(admin_token),
        )

        # Eve creates a strategy and runs backtest
        r = client.post("/api/strategies", json={
            "strategy_type": "MOVING_AVERAGE_CROSSOVER",
            "parameters": {"short_window": 5, "long_window": 20},
        }, headers=auth_header(eve_token))
        strat_id = r.json()["strategy_id"]

        r = client.post("/api/backtests", json={
            "strategy_id": strat_id, "instrument_id": inst_id,
            "start_date": "2023-01-02", "end_date": "2023-03-31",
        }, headers=auth_header(eve_token))
        eve_run_id = r.json()["run_id"]

        # Trader tries to access Eve's run → 404 (not 403 to avoid info leak)
        r = client.get(f"/api/backtests/{eve_run_id}", headers=auth_header(trader_token))
        assert r.status_code == 404
        assert r.json()["error"]["code"] == "NOT_FOUND"


class TestInsufficientData:
    def test_no_price_data_returns_422(self, client, seeded_users):
        admin_token, trader_token, _, _ = seeded_users

        # Instrument with NO prices
        r = client.post("/api/instruments", json={
            "ticker": "NODATA", "name": "No Data", "asset_class": "EQUITY",
        }, headers=auth_header(admin_token))
        inst_id = r.json()["instrument_id"]

        r = client.post("/api/strategies", json={
            "strategy_type": "MOVING_AVERAGE_CROSSOVER",
            "parameters": {"short_window": 5, "long_window": 20},
        }, headers=auth_header(trader_token))
        strat_id = r.json()["strategy_id"]

        r = client.post("/api/backtests", json={
            "strategy_id": strat_id, "instrument_id": inst_id,
            "start_date": "2023-01-02", "end_date": "2023-03-31",
        }, headers=auth_header(trader_token))
        assert r.status_code == 422
        assert r.json()["error"]["code"] == "INSUFFICIENT_DATA"

    def test_insufficient_data_no_run_row_created(self, client, seeded_users, db_session):
        """FR-10: when INSUFFICIENT_DATA is raised, NO run row must exist."""
        from app.models import BacktestRun
        admin_token, trader_token, _, _ = seeded_users

        # Count runs before
        before = db_session.query(BacktestRun).count()

        r = client.post("/api/instruments", json={
            "ticker": "ZERODATA", "name": "Zero", "asset_class": "EQUITY",
        }, headers=auth_header(admin_token))
        inst_id = r.json()["instrument_id"]

        r = client.post("/api/strategies", json={
            "strategy_type": "MOVING_AVERAGE_CROSSOVER",
            "parameters": {"short_window": 5, "long_window": 20},
        }, headers=auth_header(trader_token))
        strat_id = r.json()["strategy_id"]

        client.post("/api/backtests", json={
            "strategy_id": strat_id, "instrument_id": inst_id,
            "start_date": "2023-01-02", "end_date": "2023-03-31",
        }, headers=auth_header(trader_token))

        after = db_session.query(BacktestRun).count()
        assert after == before, "A run row was created on INSUFFICIENT_DATA — violates FR-10"

    def test_metrics_row_exists_after_completed_run(self, client, seeded_users, db_session):
        """Every COMPLETED run must have a metrics row."""
        from app.models import Metrics, BacktestRun
        admin_token, trader_token, _, _ = seeded_users

        r = client.post("/api/instruments", json={
            "ticker": "METTEST", "name": "Metrics Test", "asset_class": "EQUITY",
        }, headers=auth_header(admin_token))
        inst_id = r.json()["instrument_id"]
        csv_data = make_price_csv(n_days=60)
        client.post(
            f"/api/instruments/{inst_id}/prices",
            files={"file": ("p.csv", io.BytesIO(csv_data), "text/csv")},
            headers=auth_header(admin_token),
        )

        r = client.post("/api/strategies", json={
            "strategy_type": "MOVING_AVERAGE_CROSSOVER",
            "parameters": {"short_window": 5, "long_window": 20},
        }, headers=auth_header(trader_token))
        strat_id = r.json()["strategy_id"]

        r = client.post("/api/backtests", json={
            "strategy_id": strat_id, "instrument_id": inst_id,
            "start_date": "2023-01-02", "end_date": "2023-03-31",
        }, headers=auth_header(trader_token))
        run_id = r.json()["run_id"]

        db_session.expire_all()
        metrics = db_session.query(Metrics).filter_by(run_id=run_id).first()
        assert metrics is not None, f"No metrics row found for run {run_id}"


class TestHealthEndpoint:
    def test_health_is_public(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}
