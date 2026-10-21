from database import Base
from sqlalchemy import DateTime, Column, ForeignKey, Integer, Enum, Boolean
from sqlalchemy.orm import relationship
from sql.models.users import User
from datetime import datetime
from enumerations.user_payment_method_approvals import PaymentType, StatusType


class UserPaymentMethodApproval(Base):
    __tablename__ = "user_payment_method_approvals"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    payment_method_type = Column(
        Enum(
            PaymentType,
            values_callable=lambda x: [str(member.value) for member in PaymentType],
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
    is_default = Column(Boolean, default=False, nullable=True)
    created_at = Column(DateTime, default=datetime.now())
    created_by = Column(Integer, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True, onupdate=datetime.now())
    user = relationship("User", uselist=False)
