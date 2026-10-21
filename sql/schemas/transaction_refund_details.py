from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from sql.models.transaction_refund_details import (
    TransactionRefundDetails as TransactionRefundDetailModel,
)
from marshmallow_sqlalchemy.fields import Nested


class RefundDetailSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = TransactionRefundDetailModel
        load_instance = True
        include_relationships = True
        include_fk = True
        fields = (
            "key",
            "value",
        )


class CreateRefundDetailSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = TransactionRefundDetailModel
        load_instance = True
        include_relationships = True
        include_fk = True
        fields = (
            "transaction_refund_id",
            "key",
            "value",
            "created_at",
        )
