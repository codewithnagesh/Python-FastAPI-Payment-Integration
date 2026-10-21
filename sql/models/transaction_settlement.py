from database import Base
from sqlalchemy import DateTime, Column, ForeignKey, Integer, String, Float, Enum
from sqlalchemy.orm import relationship
from enumerations.user_payment_methods import Type
from sql.models.transactions import Transactions


class TransactionSettlement(Base):
    __tablename__ = "transaction_settlements"
    id = Column(Integer, primary_key=True)
    payment_method_type = Column(
        Enum(
            Type,
            values_callable=lambda x: [str(member.value) for member in Type],
        ),
        nullable=True,
    )
    transaction_id = Column(Integer, ForeignKey("transactions.id"))
    payment_settlement_id = Column(String(50), nullable=True)
    payment_reference_number = Column(String(50), nullable=True)
    amount = Column(Float, nullable=True)
    status = Column(String(50), nullable=True)
    refundable_amount = Column(Float, nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)
    transaction_refunds = relationship("TransactionRefund", cascade="all,delete")
    transaction = relationship("Transactions", back_populates="settlements")
