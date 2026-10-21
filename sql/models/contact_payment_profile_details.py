from datetime import datetime
from database import Base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey

# from sql.models.contact_payment_profile import ContactPaymentProfile
from sqlalchemy.orm import relationship


class ContactPaymentProfileDetails(Base):
    __tablename__ = "contact_payment_profile_details"
    id = Column(Integer, primary_key=True)
    contact_payment_profile_id = Column(
        Integer, ForeignKey("contact_payment_profiles.id")
    )
    key = Column(String, nullable=True)
    value = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now())
    updated_at = Column(DateTime, nullable=True)
    contact_profile = relationship("ContactPaymentProfile", viewonly=True)
