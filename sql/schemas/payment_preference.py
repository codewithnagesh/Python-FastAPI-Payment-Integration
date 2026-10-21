from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from sql.models.payment_preference import PaymentPreference as PaymentPreferenceModel
from sql.models.users import User as UserModel
from marshmallow_sqlalchemy.fields import Nested


class UserSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = UserModel
        load_instance = True
        include_relationships = True
        include_fk = True
        fields = (
            "id",
            "name",
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
            "payment_method_type",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
            "active",
        )

    user = Nested(UserSchema(), dump_only=True)


class CreatePaymentPreferenceSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = PaymentPreferenceModel
        load_instance = True
        include_relationships = True
        include_fk = True
        fields = (
            "user_id",
            "preference_type",
            "payment_method_type",
            "created_by",
            "active",
        )


class UpdatePaymentPreferenceSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = PaymentPreferenceModel
        load_instance = True
        include_relationships = True
        include_fk = True
        fields = (
            "updated_by",
            "active",
        )
