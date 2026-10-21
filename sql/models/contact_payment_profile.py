from datetime import datetime
from database import Base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sql.models.users import User
from sql.models.contact_payment_profile_details import ContactPaymentProfileDetails
from sqlalchemy.orm import relationship
from enumerations.user_payment_methods import Type


class ContactPaymentProfile(Base):
    __tablename__ = "contact_payment_profiles"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"))
    profile_id = Column(String, nullable=False)
    payment_profile_id = Column(String, nullable=False)
    reference_number = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now(), nullable=False)
    updated_at = Column(DateTime, nullable=True)
    user = relationship("User", uselist=False)
    profile_details = relationship(
        "ContactPaymentProfileDetails", back_populates="contact_profile", uselist=True
    )
    payment_method_type = Column(
        Enum(
            Type,
            values_callable=lambda x: [str(member.value) for member in Type],
        ),
        nullable=True,
        default=Type.PAYSAFE,
    )
