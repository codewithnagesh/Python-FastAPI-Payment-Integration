from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from sql.models.contact_payment_profile import (
    ContactPaymentProfile as ContactPaymentProfileModel,
)
from marshmallow_sqlalchemy.fields import Nested
from sql.schemas.contact_payment_profile_details import (
    ContactPaymentProfileDetailSchema,
)
from sql.models.contact import Contact as ContactModel
from sql.schemas.user.user import UserTransactionSchema


class ContactSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ContactModel
        load_instance = True
        include_relationships = True
        include_fk = True
        fields = (
            "id",
            "first_name",
            "last_name",
            "email",
            "user",
        )

    user = Nested(UserTransactionSchema())


class ContactPaymentProfileSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ContactPaymentProfileModel
        load_instance = True
        include_relationships = True
        include_fk = True
        fields = (
            "id",
            "contact",
            "profile_id",
            "payment_profile_id",
            "reference_number",
            "profile_details",
            "payment_method_type",
            "created_at",
            "updated_at",
        )

    contact = Nested(ContactSchema())
    profile_details = Nested(ContactPaymentProfileDetailSchema(), many=True)


class CreateContactPaymentProfileSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ContactPaymentProfileModel
        load_instance = True
        include_relationships = True
        include_fk = True
        fields = (
            "user_id",
            "profile_id",
            "payment_profile_id",
            "reference_number",
            "payment_method_type",
            "created_at",
        )


class UpdateContactPaymentProfileSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ContactPaymentProfileModel
        load_instance = True
        include_relationships = True
        include_fk = True
        fields = (
            "user_id",
            "profile_id",
            "payment_profile_id",
            "reference_number",
            "payment_method_type",
            "updated_at",
        )
