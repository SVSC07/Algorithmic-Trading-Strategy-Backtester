from dataclasses import dataclass
from datetime import date

@dataclass
class Signal:
    date: date
    action: str        # "BUY" or "SELL"
    price: float       # close of that day

@dataclass
class TradeRecord:
    entry_date: date
    exit_date: date
    entry_price: float
    exit_price: float
    quantity: int
    pnl: float

@dataclass
class EquityPoint:
    date: date
    equity: float

@dataclass
class MetricsResult:
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    cagr: float
    total_return: float

class ValidationError(Exception): ...         # HTTP 400
class AuthError(Exception): ...               # HTTP 401
class ForbiddenError(Exception): ...          # HTTP 403
class NotFoundError(Exception): ...           # HTTP 404
class ConflictError(Exception): ...           # HTTP 409
class InsufficientDataError(Exception): ...   # HTTP 422
