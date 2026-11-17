from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.persistence.models import User
from backend.persistence.repositories.base import BaseRepo, repo_method


class UserRepo(BaseRepo):
    @repo_method
    def create_user(
        self,
        username: str,
        email: str,
        password_hash: str,
        role: str = "trader",
        session: Optional[Session] = None,
    ) -> User:
        """Create a new user with the given credentials and role."""
        with self.get_db(session) as s:
            user = User(
                username=username,
                email=email,
                password_hash=password_hash,
                role=role,
            )
            s.add(user)
            s.flush()
            # Ensure attributes are loaded if detached
            s.refresh(user)
            return user

    @repo_method
    def get_by_username(
        self,
        username: str,
        session: Optional[Session] = None,
    ) -> Optional[User]:
        """Fetch user by username or return None."""
        with self.get_db(session) as s:
            stmt = select(User).where(User.username == username)
            return s.execute(stmt).scalar_one_or_none()
