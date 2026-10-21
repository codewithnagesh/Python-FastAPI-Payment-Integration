from database import Base
from sqlalchemy import DateTime, Column, Integer, Boolean, Enum, ForeignKey
from enumerations.payment_preference import PreferenceType
from enumerations.user_payment_methods import Type
from sqlalchemy.orm import relationship
from datetime import datetime


class PaymentPreference(Base):
    __tablename__ = "payment_preferences"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"))
    preference_type = Column(
        Enum(
            PreferenceType,
            values_callable=lambda x: [str(member.value) for member in PreferenceType],
        ),
        nullable=True,
    )
    payment_method_type = Column(
        Enum(Type, values_callable=lambda x: [str(member.value) for member in Type])
    )
    active = Column(Boolean, default=False)
    created_at = Column(DateTime, nullable=True, default=datetime.now())
    created_by = Column(Integer, nullable=True)
    updated_at = Column(DateTime, nullable=True, onupdate=datetime.now())
    updated_by = Column(Integer, nullable=True)
    user = relationship("User", uselist=False)
