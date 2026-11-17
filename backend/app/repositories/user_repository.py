# STUB — owned by Rishabh, replaced on merge
"""
repositories/user_repository.py
UserRepository stub matching the contract interface.
"""
from typing import Optional

from sqlalchemy.orm import Session

from app.models import User


class UserRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, user: User) -> User:
        self._session.add(user)
        self._session.flush()
        return user

    def find_by_email(self, email: str) -> Optional[User]:
        return self._session.query(User).filter_by(email=email).first()

    def find_by_id(self, user_id: int) -> Optional[User]:
        return self._session.query(User).filter_by(user_id=user_id).first()
