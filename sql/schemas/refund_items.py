from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from sql.models.invoice_items import InvoiceItems as InvoiceItemsModel
from sql.models.refund_items import RefundItems as RefundItemsModel
from marshmallow_sqlalchemy.fields import Nested


class InvoiceItemSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = InvoiceItemsModel
        load_instance = True
        include_relationships = True
        include_fk = True
        fields = (
            "id",
            "price",
            "quantity",
            "is_taxable",
            "total_amount",
        )


class CreateRefundItemsSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = RefundItemsModel
        load_instance = True
        include_relationships = True
        include_fk = True
        fields = (
            "id",
            "transaction_refund_id",
            "invoice_item_id",
            "quantity",
            "price",
            "is_taxable",
            "tax_rate",
            "total_amount",
            "created_at",
        )


class RefundItemsSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = RefundItemsModel
        load_instance = True
        include_relationships = True
        include_fk = True
        fields = (
            "id",
            "invoice_item",
            "quantity",
            "price",
            "is_taxable",
            "tax_rate",
            "total_amount",
        )

    invoice_item = Nested(InvoiceItemSchema())