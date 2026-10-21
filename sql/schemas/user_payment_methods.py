from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from sql.models.user_payment_methods import UserPaymentMethods as UserPaymentMethodModel
from sql.models.users import User as UserModel
from sql.models.payment_preference import PaymentPreference as PaymentPreferenceModel
from sql.schemas.user_payment_method_options import UserPaymentMethodOptionSchema
from marshmallow_sqlalchemy.fields import Nested


class UserSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = UserModel
        load_instance = True
        include_relationships = True
        include_fk = True
        fields = (
            "id",
            "first_name",
            "last_name",
            "active",
            "username"
        )


class PaymentPreferenceSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = PaymentPreferenceModel
        load_instance = True
        include_relationships = True
        include_fk = True
        fields = (
            "id",
            "user",
            "preference_type",
            "active",
        )

    user = Nested(UserSchema(), dump_only=True)


class UserPaymentMethodSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = UserPaymentMethodModel
        load_instance = True
        include_relationships = True
        include_fk = True
        fields = (
            "id",
            "payment_preference",
            "user",
            "payment_method_type",
            "status",
            "payment_method_options",
            "is_default",
            "created_at",
            "created_by",
            "updated_at",
        )

    payment_preference = Nested(PaymentPreferenceSchema(), dump_only=True)
    user = Nested(UserSchema(), dump_only=True)
    payment_method_options = Nested(UserPaymentMethodOptionSchema(), many=True)


class CreateUserPaymentMethodSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = UserPaymentMethodModel
        load_instance = True
        include_relationships = True
        include_fk = True
        fields = (
            "payment_preference_id",
            "user_id",
            "payment_method_type",
            "status",
            "is_default",
            "created_at",
            "created_by",
            "deleted_at",
            "deleted_by",
        )


class UpdateUserPaymentMethodSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = UserPaymentMethodModel
        load_instance = True
        include_relationships = True
        include_fk = True
        fields = ("status","is_default", "updated_at", "updated_by")


class UpdateAuthnetUserPaymentMethodSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = UserPaymentMethodModel
        load_instance = True
        include_relationships = True
        include_fk = True
        fields = (
            "payment_preference_id",
            "user_id",
            "payment_method_type",
            "status",
            "updated_at",
            "updated_by",
        )
