from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from sql.models.user_payment_method_approvals import (
    UserPaymentMethodApproval as UserPaymentMethodApprovalModel,
)
from marshmallow_sqlalchemy.fields import Nested
from sql.models.users import User as UserModel


class UserSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = UserModel
        load_instance = True
        include_relationships = True
        include_fk = True
        fields = ("id", "first_name", "last_name", "username", "active")



class UserPaymentMethodApprovalSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = UserPaymentMethodApprovalModel
        load_instance = True
        include_relationships = True
        include_fk = True
        fields = (
            "id",
            "user",
            "payment_method_type",
            "status",
            "is_default",
            "created_at",
            "created_by",
            "approved_at",
            "updated_at",
        )

    user = Nested(UserSchema(), dump_only=True)


class CreateUserPaymentMethodApprovalModelSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = UserPaymentMethodApprovalModel
        load_instance = True
        include_relationships = True
        include_fk = True
        fields = (
            "id",
            "user_id",
            "payment_method_type",
            "status",
            "is_default",
            "created_at",
            "created_by",
            "approved_at",
        )


class EditUserPaymentMethodApprovaStatuslSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = UserPaymentMethodApprovalModel
        load_instance = True
        include_relationships = True
        include_fk = True
        fields = ("id", "status", "approved_at", "updated_at")
