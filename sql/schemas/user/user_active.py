from marshmallow import fields
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from marshmallow_sqlalchemy.fields import Nested
from pydantic import BaseModel
from typing import List
from sql.models.users import User as UserModel






class ActiveUserModel(BaseModel):
    id: int
    username: str
    roles: List[str]
    active: bool

class UserActiveSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = UserModel
        load_instance = True
        include_relationships = True
        include_fk = True
        fields = (
            "id",
            "username",
            "roles",
            "active",
        )

    def features_cus(self, obj):
        if hasattr(obj, "features"):
            return obj.features.split(",")
        return None
