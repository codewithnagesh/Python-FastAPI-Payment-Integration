from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from sql.models.transaction_settlement import (
    TransactionSettlement as TransactionSettlementModel,
)
from marshmallow_sqlalchemy.fields import Nested
from sql.schemas.transaction_refunds import TransactionRefundSchema


class SettlementSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = TransactionSettlementModel
        load_instance = True
        include_relationships = True
        include_fk = True
        fields = (
            "id",
            "payment_method_type",
            "payment_settlement_id",
            "payment_reference_number",
            "amount",
            "status",
            "refundable_amount",
            "transaction_refunds",
            "created_at",
            "updated_at",
        )

    transaction_refunds = Nested(TransactionRefundSchema(), many=True)


class CreateSettlementSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = TransactionSettlementModel
        load_instance = True
        include_relationships = True
        include_fk = True
        fields = (
            "payment_method_type",
            "transaction_id",
            "payment_settlement_id",
            "payment_reference_number",
            "amount",
            "refundable_amount",
            "status",
            "created_at",
        )


class UpdateSettlementSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = TransactionSettlementModel
        load_instance = True
        include_relationships = True
        include_fk = True
        fields = (
            "status",
            "updated_at",
        )
