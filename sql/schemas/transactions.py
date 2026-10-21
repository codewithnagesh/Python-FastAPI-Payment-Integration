from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from sql.models.transactions import Transactions as TransactionModel
from marshmallow_sqlalchemy.fields import Nested
from sql.schemas.transaction_details import TransactionDetailsSchema
from sql.schemas.user.user import UserTransactionSchema
from sql.schemas.transaction_settlement import SettlementSchema
from sql.models.contact import Contact
from sql.models.invoice import Invoice


class ContactTransactionSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Contact
        load_instance = True
        include_relationships = True
        include_fk = True
        fields = ("id", "first_name", "last_name", "email")


class InvoiceTransactionSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Invoice
        load_instance = True
        include_relationships = True
        include_fk = True
        fields = ("id", "invoice_number", "total_invoice_amount", "status")


class TransactionSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = TransactionModel
        load_instance = True
        include_relationships = True
        include_fk = True
        fields = (
            "id",
            "payment_method_type",
            "payment_transaction_id",
            "payment_reference_number",
            "user_payment_method_id",
            "contact_payment_profile_id",
            "user",
            "contact",
            "invoice",
            "status",
            "amount",
            "settlements",
            "transaction_details",
            "created_at",
            "updated_at",
        )

    settlements = Nested(SettlementSchema(), many=True)
    user = Nested(UserTransactionSchema())
    contact = Nested(ContactTransactionSchema())
    invoice = Nested(InvoiceTransactionSchema())
    transaction_details = Nested(TransactionDetailsSchema(), many=True)


class CreateTransactionSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = TransactionModel
        load_instance = True
        include_relationships = True
        include_fk = True
        fields = (
            "payment_transaction_id",
            "payment_reference_number",
            "user_payment_method_id",
            "contact_payment_profile_id",
            "payment_method_type",
            "invoice_id",
            "user_id",
            "status",
            "amount",
            "created_at",
        )


class UpdateTransactionSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = TransactionModel
        load_instance = True
        include_relationships = True
        include_fk = True
        fields = (
            "status",
            "updated_at",
        )
