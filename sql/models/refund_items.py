from database import Base
from sqlalchemy import DateTime, Column, ForeignKey, Integer, Boolean, Float, Text
from sqlalchemy.orm import relationship, backref
from datetime import datetime


class RefundItems(Base):
    __tablename__ = "refund_items"
    id = Column(Integer, primary_key=True)
    transaction_refund_id = Column(Integer, ForeignKey("transaction_refunds.id"))
    invoice_item_id = Column(Integer, ForeignKey("invoice_items.id"))
    quantity = Column(Integer, nullable=True)
    price = Column(Float, nullable=True)
    is_taxable = Column(Boolean, nullable=True)
    tax_rate = Column(Float, default=0, nullable=True)
    total_amount = Column(Float, nullable=True)
    created_at = Column(DateTime, nullable=True)
    invoice_item = relationship("InvoiceItems")
    transaction_refund = relationship(
        "TransactionRefund", back_populates="refund_items"
    )