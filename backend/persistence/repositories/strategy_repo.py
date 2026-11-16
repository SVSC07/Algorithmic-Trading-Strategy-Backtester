import json
from typing import Optional, List, Dict, Any
from sqlalchemy import select, delete
from sqlalchemy.orm import Session, selectinload

from backend.persistence.models import Strategy, StrategyParameter
from backend.persistence.repositories.base import BaseRepo, repo_method


def serialize_param_value(val: Any) -> str:
    """Serialize parameter value to JSON string."""
    try:
        return json.dumps(val)
    except Exception:
        return str(val)


def deserialize_param_value(val: str) -> Any:
    """Deserialize parameter value from JSON string or return raw string."""
    try:
        return json.loads(val)
    except Exception:
        return val


def format_strategy_dict(strategy: Strategy) -> Dict[str, Any]:
    params = {}
    if strategy.parameters:
        for p in strategy.parameters:
            params[p.param_name] = deserialize_param_value(p.param_value)
    return {
        "id": strategy.id,
        "user_id": strategy.user_id,
        "name": strategy.name,
        "type": strategy.type,
        "parameters": params,
        "created_at": strategy.created_at,
    }


class StrategyRepo(BaseRepo):
    @repo_method
    def create_strategy(
        self,
        user_id: int,
        name: str,
        type: str,
        parameters: Optional[Dict[str, Any]] = None,
        session: Optional[Session] = None,
    ) -> Dict[str, Any]:
        """Create a new strategy and its parameters in one atomic transaction."""
        params = parameters or {}
        with self.get_db(session) as s:
            strategy = Strategy(
                user_id=user_id,
                name=name,
                type=type,
            )
            s.add(strategy)
            s.flush()

            for p_name, p_val in params.items():
                param_row = StrategyParameter(
                    strategy_id=strategy.id,
                    param_name=p_name,
                    param_value=serialize_param_value(p_val),
                )
                s.add(param_row)

            s.flush()
            s.refresh(strategy)
            return format_strategy_dict(strategy)

    @repo_method
    def get_strategy(
        self,
        id: int,
        session: Optional[Session] = None,
    ) -> Optional[Dict[str, Any]]:
        """Fetch strategy by ID with its parameters, returning a plain dict."""
        with self.get_db(session) as s:
            stmt = (
                select(Strategy)
                .options(selectinload(Strategy.parameters))
                .where(Strategy.id == id)
            )
            strategy = s.execute(stmt).scalar_one_or_none()
            if not strategy:
                return None
            return format_strategy_dict(strategy)

    @repo_method
    def list_strategies(
        self,
        user_id: int,
        session: Optional[Session] = None,
    ) -> List[Dict[str, Any]]:
        """List all strategies belonging to a user, with their parameters."""
        with self.get_db(session) as s:
            stmt = (
                select(Strategy)
                .options(selectinload(Strategy.parameters))
                .where(Strategy.user_id == user_id)
                .order_by(Strategy.id.asc())
            )
            strategies = s.execute(stmt).scalars().all()
            return [format_strategy_dict(st) for st in strategies]

    @repo_method
    def update_strategy(
        self,
        id: int,
        name: Optional[str] = None,
        type: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        session: Optional[Session] = None,
    ) -> Optional[Dict[str, Any]]:
        """Update strategy metadata and replace parameters if provided."""
        with self.get_db(session) as s:
            stmt = (
                select(Strategy)
                .options(selectinload(Strategy.parameters))
                .where(Strategy.id == id)
            )
            strategy = s.execute(stmt).scalar_one_or_none()
            if not strategy:
                return None

            if name is not None:
                strategy.name = name
            if type is not None:
                strategy.type = type

            if parameters is not None:
                # Remove existing parameters and re-add updated set
                strategy.parameters.clear()
                s.flush()
                for p_name, p_val in parameters.items():
                    s.add(
                        StrategyParameter(
                            strategy_id=strategy.id,
                            param_name=p_name,
                            param_value=serialize_param_value(p_val),
                        )
                    )

            s.flush()
            s.refresh(strategy)
            return format_strategy_dict(strategy)

    @repo_method
    def delete_strategy(
        self,
        id: int,
        session: Optional[Session] = None,
    ) -> None:
        """Delete a strategy by ID (cascades to StrategyParameter and BacktestRun)."""
        with self.get_db(session) as s:
            st = s.get(Strategy, id)
            if st:
                s.delete(st)
                s.flush()
