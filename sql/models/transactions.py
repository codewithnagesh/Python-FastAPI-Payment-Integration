# This module defines the Transactions SQLAlchemy model for the payment API service.
# It represents the database table structure for payment transactions and their relationships.

from database import Base  # Base class for SQLAlchemy models
from sqlalchemy import DateTime, Column, ForeignKey, Integer, String, Float, Enum  # SQLAlchemy column types
from sqlalchemy.orm import relationship  # SQLAlchemy relationship definitions
from sql.models.user_payment_methods import UserPaymentMethods  # User payment methods model
from sql.models.contact_payment_profile import ContactPaymentProfile  # Contact payment profile model
from sql.models.users import User  # User model
from sql.models.invoice import Invoice  # Invoice model
from datetime import datetime  # For timestamp fields
from enumerations.user_payment_methods import Type  # Enum for payment types


class Transactions(Base):
    """
    SQLAlchemy model representing payment transactions in the database.
    
    This model stores information about payment transactions including
    payment method details, amounts, status, and relationships to users,
    invoices, and payment profiles.
    """
    __tablename__ = "transactions"  # Database table name
    
    # Primary key
    id = Column(Integer, primary_key=True)
    
    # Payment method type (authnet, paysafe, etc.)
    payment_method_type = Column(
        Enum(
            Type,
            values_callable=lambda x: [str(member.value) for member in Type],
        ),
        nullable=True,
    )
    
    # External payment processor transaction ID
    payment_transaction_id = Column(String, nullable=True)
    
    # Merchant reference number for tracking
    payment_reference_number = Column(String, nullable=True)
    
    # Foreign key relationships
    user_payment_method_id = Column(Integer, ForeignKey("user_payment_methods.id"))  # User's payment method
    contact_payment_profile_id = Column(
        Integer, ForeignKey("contact_payment_profiles.id")  # Contact payment profile
    )
    user_id = Column(Integer, ForeignKey("users.id"))  # User who made the transaction
    invoice_id = Column(Integer, ForeignKey("invoices.id"))  # Invoice being paid

    # Transaction details
    status = Column(String(50), nullable=True)  # Transaction status (completed, pending, failed, etc.)
    amount = Column(Float, nullable=True)  # Transaction amount
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.now())  # Transaction creation time
    updated_at = Column(DateTime, nullable=True)  # Last update time
    
    # SQLAlchemy relationships
    user_payment_method = relationship("UserPaymentMethods")  # Related user payment method
    contact_payment_profile = relationship("ContactPaymentProfile")  # Related contact payment profile
    user = relationship("User")  # Related user
    contact = relationship("Contact")  # Related contact
    invoice = relationship("Invoice")  # Related invoice
    transaction_details = relationship("TransactionDetails", cascade="all,delete")  # Transaction details (cascade delete)
    settlements = relationship(
        "TransactionSettlement", back_populates="transaction", cascade="all,delete"  # Settlement records (cascade delete)
    )
