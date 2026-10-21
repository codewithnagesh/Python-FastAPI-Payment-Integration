from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from pydantic import BaseModel, EmailStr
from marshmallow import fields
from sql.models.users import User as UserModel
from marshmallow_sqlalchemy.fields import Nested


class UserBase(BaseModel):
    username: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int
    active: bool

    class Config:
        orm_mode = True


class ActiveUser(BaseModel):
    id: int
    username: EmailStr