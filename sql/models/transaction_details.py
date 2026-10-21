from database import Base
from sqlalchemy import DateTime, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship, backref
from sql.models.transactions import Transactions
from datetime import datetime


class TransactionDetails(Base):
    __tablename__ = "transaction_details"
    id = Column(Integer, primary_key=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"))
    key = Column(String, nullable=True)
    value = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now())
    updated_at = Column(DateTime, nullable=True)
    transactions = relationship(
        "Transactions", viewonly=True
    )  # , backref="transaction_details"
