from database import Base
from sqlalchemy import DateTime, Column, ForeignKey, Integer, String, Float, Enum
from sqlalchemy.orm import relationship
from sql.models.transactions import Transactions
from sql.models.transaction_settlement import TransactionSettlement
from datetime import datetime
from enumerations.user_payment_methods import Type


class TransactionRefund(Base):
    __tablename__ = "transaction_refunds"
    id = Column(Integer, primary_key=True)
    payment_method_type = Column(
        Enum(
            Type,
            values_callable=lambda x: [str(member.value) for member in Type],
        ),
        nullable=True,
        default=Type.PAYSAFE,
    )
    transaction_id = Column(Integer, ForeignKey("transactions.id"))
    transaction_settlement_id = Column(
        Integer, ForeignKey("transaction_settlements.id")
    )
    invoice_id = Column(Integer, ForeignKey("invoices.id"))
    payment_refund_id = Column(String, nullable=True)
    status = Column(String(50), nullable=True)
    amount = Column(Float, nullable=True)
    reference_number = Column(String(50), nullable=True)
    created_by = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)
    transaction = relationship("Transactions")
    transaction_refund_details = relationship("TransactionRefundDetails")
    transaction_settlement = relationship("TransactionSettlement", viewonly=True)
    refund_items = relationship("RefundItems", cascade="all, delete")