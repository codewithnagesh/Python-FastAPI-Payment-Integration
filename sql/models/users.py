from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text, Float, JSON
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, nullable=False, unique=True)
    active = Column(Boolean, nullable=False)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    invoice_tax_rate = Column(
        Float(precision=None, asdecimal=False, decimal_return_scale=2)
    )
    