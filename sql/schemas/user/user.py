from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from marshmallow import fields
import json
from pydantic import BaseModel, EmailStr
from marshmallow import fields
from sql.models.users import User as UserModel
from sql.schemas.plan import Plan
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


class UserSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = UserModel
        load_instance = True
        include_relationships = True
        include_fk = True
        fields = (
            "id",
            "active",
            "username",
            "first_name",
            "last_name",
            "timezone",
        )


class UserSchemaTimeZone(SQLAlchemyAutoSchema):
    class Meta:
        model = UserModel
        load_instance = True
        include_relationships = True
        include_fk = True
        fields = ("id", "active", "username", "timezone")


class UserUpdateSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = UserModel
        load_instance = True
        include_relationships = True
        include_fk = True
        fields = (
            "first_name",
            "last_name",
            "username",
            "active",
        )

class UserListSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = UserModel
        load_instance = True
        include_relationships = True
        include_fk = True
        fields = (
            "id",
            "name",
            "username",
        )

    name = fields.Method("name_cus")

    def name_cus(self, obj):
        name = None
        if hasattr(obj, "first_name"):
            if obj.first_name is not None:
                name = obj.first_name
        if hasattr(obj, "last_name") and name:
            if obj.last_name is not None:
                name = name + " " + obj.last_name
        return name


class UserDetailsSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = UserModel
        load_instance = True
        include_relationships = True
        include_fk = True
        fields = (
            "id",
            "username",
            "first_name",
            "last_name",
            "created",
            "timezone",
        )


class ReadUserDataSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = UserModel
        load_instance = True
        include_relationships = True
        include_fk = True
        fields = (
            "id",
            "username",
            "first_name",
            "last_name",
            "active",
            "created",
            "invoice_tax_rate",
            "timezone",
        )


class UserTransactionSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = UserModel
        load_instance = True
        include_relationships = True
        include_fk = True
        fields = ("id", "first_name", "last_name", "username")

