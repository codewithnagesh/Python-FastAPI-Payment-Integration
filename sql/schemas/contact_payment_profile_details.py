from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from sql.models.contact_payment_profile_details import (
    ContactPaymentProfileDetails as ContactPaymentProfileDetailModel,
)


class ContactPaymentProfileDetailSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ContactPaymentProfileDetailModel
        load_instance = True
        include_relationships = True
        include_fk = True
        fields = (
            "id",
            "key",
            "value",
            "created_at",
        )


class CreateContactPaymentProfileDetailSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ContactPaymentProfileDetailModel
        load_instance = True
        include_relationships = True
        include_fk = True
        fields = (
            "contact_payment_profile_id",
            "key",
            "value",
            "created_at",
            "updated_at",
        )


class UpdateContactPaymentProfileDetailSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ContactPaymentProfileDetailModel
        load_instance = True
        include_relationships = True
        include_fk = True
        fields = (
            "contact_payment_profile_id",
            "key",
            "value",
            "updated_at",
        )
