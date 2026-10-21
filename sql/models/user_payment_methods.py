from database import Base
from sqlalchemy import DateTime, Column, ForeignKey, Integer, Enum, Boolean
from sqlalchemy.orm import relationship
from sql.models.users import User
from sql.models.payment_preference import PaymentPreference
from datetime import datetime
from enumerations.user_payment_methods import Type, StatusType


class UserPaymentMethods(Base):
    __tablename__ = "user_payment_methods"

    id = Column(Integer, primary_key=True)
    payment_preference_id = Column(Integer, ForeignKey("payment_preferences.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    payment_method_type = Column(
        Enum(
            Type,
            values_callable=lambda x: [str(member.value) for member in Type],
        ),
        nullable=True,
    )
    status = Column(
        Enum(
            StatusType,
            values_callable=lambda x: [str(member.value) for member in StatusType],
        ),
        nullable=True,
    )
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now())
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
    updated_at = Column(DateTime, nullable=True)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(Integer, nullable=True)
    payment_preference = relationship("PaymentPreference", uselist=False)
    user = relationship("User", uselist=False)
    payment_method_options = relationship(
        "UserPaymentMethodOptions", back_populates="user_payment_methods", uselist=True
    )
