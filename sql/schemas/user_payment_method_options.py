from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from sql.models.user_payment_method_options import (
    UserPaymentMethodOptions as UserPaymentMethodOptionModel,
)


class UserPaymentMethodOptionSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = UserPaymentMethodOptionModel
        load_instance = True
        include_relationships = True
        include_fk = True
        fields = (
            "key",
            "value",
        )


class CreateUserPaymentMethodOptionSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = UserPaymentMethodOptionModel
        load_instance = True
        include_relationships = True
        include_fk = True
        fields = (
            "user_payment_method_id",
            "key",
            "value",
            "created_at",
        )


class UpdateUserPaymentMethodOptionSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = UserPaymentMethodOptionModel
        load_instance = True
        include_relationships = True
        include_fk = True
        fields = (
            "user_payment_method_id",
            "key",
            "value",
            "updated_at",
        )
