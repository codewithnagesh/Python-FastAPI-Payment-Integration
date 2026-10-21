from sqlalchemy import and_
from sqlalchemy.orm import Session
from sql.models import users
from sql.models.users import User as UserModel


def get_user(db: Session, user_id: int):
    return db.query(users.User).filter(users.User.id == user_id).first()

