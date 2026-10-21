from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from sql.models.transaction_refunds import TransactionRefund as TransactionRefundModel
from marshmallow_sqlalchemy.fields import Nested
from sql.schemas.transaction_refund_details import RefundDetailSchema
from sql.schemas.refund_items import RefundItemsSchema


class TransactionRefundSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = TransactionRefundModel
        load_instance = True
        include_relationships = True
        include_fk = True
        fields = (
            "id",
            "payment_method_type",
            "payment_refund_id",
            "reference_number",
            "status",
            "amount",
            "transaction_refund_details",
            "refund_items",
            "created_by",
            "created_at",
            "updated_at",
        )

    transaction_refund_details = Nested(RefundDetailSchema(), many=True)
    refund_items = Nested(RefundItemsSchema(), many=True)


class RefundProcessSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = TransactionRefundModel
        load_instance = True
        include_relationships = True
        include_fk = True
        fields = (
            "id",
            "payment_method_type",
            "transaction_id",
            "transaction_settlement_id",
            "payment_refund_id",
            "reference_number",
            "invoice_id",
            "status",
            "amount",
            "created_by",
            "created_at",
        )


class UpdateRefundSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = TransactionRefundModel
        load_instance = True
        include_relationships = True
        include_fk = True
        fields = (
            "status",
            "updated_at",
        )