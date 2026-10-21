from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from sql.models.transaction_details import TransactionDetails as TransactionDetailsModel
from marshmallow_sqlalchemy.fields import Nested


class TransactionDetailsSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = TransactionDetailsModel
        load_instance = True
        include_relationships = True
        include_fk = True
        fields = (
            "key",
            "value",
        )


class CreateTransactionDetailsSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = TransactionDetailsModel
        load_instance = True
        include_relationships = True
        include_fk = True
        fields = (
            "transaction_id",
            "key",
            "value",
            "created_at",
        )
