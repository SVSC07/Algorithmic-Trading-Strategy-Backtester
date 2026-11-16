from contextlib import contextmanager
from typing import Optional, Generator, Callable, Any
from sqlalchemy.orm import Session
from backend.persistence.database import SessionLocal


class repo_method:
    """Descriptor that allows repository methods to be invoked either on an instance
    (e.g., repo.method(...)) or directly on the class (e.g., Repo.method(...)).
    """

    def __init__(self, func: Callable):
        self.func = func
        self.__doc__ = func.__doc__
        self.__name__ = func.__name__

    def __get__(self, instance: Any, owner: Any) -> Callable:
        if instance is not None:
            return lambda *args, **kwargs: self.func(instance, *args, **kwargs)
        default_inst = owner()
        return lambda *args, **kwargs: self.func(default_inst, *args, **kwargs)


class BaseRepo:
    def __init__(self, session: Optional[Session] = None):
        self._session = session

    @contextmanager
    def get_db(self, session_override: Optional[Session] = None) -> Generator[Session, None, None]:
        if session_override is not None:
            yield session_override
        elif self._session is not None:
            yield self._session
        else:
            s = SessionLocal()
            try:
                yield s
                s.commit()
            except Exception:
                s.rollback()
                raise
            finally:
                s.close()
