from database import Base
from sqlalchemy import DateTime, Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sql.models.transaction_refunds import TransactionRefund


class TransactionRefundDetails(Base):
    __tablename__ = "transaction_refund_details"
    id = Column(Integer, primary_key=True)
    transaction_refund_id = Column(Integer, ForeignKey("transaction_refunds.id"))
    key = Column(String, nullable=True)
    value = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=True)
    transaction_refund = relationship("TransactionRefund", viewonly=True)