from typing import Optional
from infrastructure.models.db_models import User
from extensions import db

class UserRepository:
    def get_by_email(self, email: str) -> Optional[User]:
        return User.query.filter_by(email=email).first()
        
    def get_by_phone(self, phone: str) -> Optional[User]:
        return User.query.filter_by(phone=phone).first()

    def get_by_id(self, user_id: int) -> Optional[User]:
        return User.query.get(user_id)

    def save(self, user: User) -> User:
        db.session.add(user)
        db.session.commit()
        return user