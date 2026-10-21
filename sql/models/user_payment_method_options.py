from datetime import datetime
from database import Base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship, backref
from sql.models.user_payment_methods import UserPaymentMethods


class UserPaymentMethodOptions(Base):
    __tablename__ = "user_payment_method_options"
    id = Column(Integer, primary_key=True)
    user_payment_method_id = Column(Integer, ForeignKey("user_payment_methods.id"))
    key = Column(String, nullable=True)
    value = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now())
    updated_at = Column(DateTime, nullable=True)
    user_payment_methods = relationship(
        "UserPaymentMethods", back_populates="payment_method_options"
    )
