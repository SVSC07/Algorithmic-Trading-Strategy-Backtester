# STUB, owned by Rishabh, replaced on merge
from sqlalchemy.orm import Session
from app.models.user import User

class UserRepository:
    def __init__(self, session: Session):
        self.session = session

    def save(self, user: User) -> User:
        self.session.add(user)
        self.session.flush()
        return user

    def find_by_email(self, email: str) -> User | None:
        return self.session.query(User).filter(User.email == email).first()

    def find_by_id(self, user_id: int) -> User | None:
        return self.session.query(User).filter(User.user_id == user_id).first()
