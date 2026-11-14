# STUB, owned by Molik, replaced on merge
from app.domain import ValidationError, AuthError, ConflictError
from app.models.user import User
from app.core.security import hash_password, verify_password, create_token, decode_token

class AuthService:
    def __init__(self, session, user_repo):
        self.session = session
        self.user_repo = user_repo

    def register(self, name: str, email: str, password: str) -> User:
        if not name or not name.strip():
            raise ValidationError("Name is required")
        if not email or "@" not in email:
            raise ValidationError("Valid email is required")
        if not password or len(password) < 8:
            raise ValidationError("Password must be at least 8 characters long")

        existing = self.user_repo.find_by_email(email.strip().lower())
        if existing:
            raise ConflictError("Email already registered")

        hashed = hash_password(password)
        user = User(
            name=name.strip(),
            email=email.strip().lower(),
            password_hash=hashed,
            role="TRADER",
        )
        saved = self.user_repo.save(user)
        self.session.commit()
        return saved

    def login(self, email: str, password: str) -> tuple[str, User]:
        if not email or not password:
            raise AuthError("Email and password are required")

        user = self.user_repo.find_by_email(email.strip().lower())
        if not user or not verify_password(password, user.password_hash):
            raise AuthError("Invalid email or password")

        token = create_token(user.user_id, user.role)
        return token, user

    def user_from_token(self, token: str) -> User:
        payload = decode_token(token)
        user_id = payload.get("user_id") or payload.get("sub")
        if not user_id:
            raise AuthError("Token missing user identifier")

        user = self.user_repo.find_by_id(int(user_id))
        if not user:
            raise AuthError("User not found")
        return user
