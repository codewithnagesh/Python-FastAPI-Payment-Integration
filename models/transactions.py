# This module defines Pydantic models for transaction-related operations in the payment API service.
# These models handle payment processing, refunds, and transaction management across multiple payment providers.

from __future__ import annotations
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field, validator


class Type(str, Enum):
    """
    Enumeration of supported payment method types.
    
    This enum defines all the payment providers and methods supported by the system,
    including traditional payment processors and modern digital wallets.
    """
    authnet = "authnet"      # Authorize.Net payment processor
    paysafe = "paysafe"      # Paysafe payment processor
    jupiter = "jupiter"      # Jupiter payment processor
    stripe = "stripe"        # Stripe payment processor
    paypal = "paypal"        # PayPal payment processor
    googlepay = "googlepay"  # Google Pay digital wallet
    applepay = "applepay"    # Apple Pay digital wallet


class ProfilePayment(BaseModel):
    """
    Model for profile-based payment processing.
    
    This model is used for payments that are processed using stored payment profiles
    (like subscription payments or recurring billing).
    """
    user_id: int = Field(gt=0, description="ID of the user making the payment")
    invoice_id: int = Field(gt=0, description="ID of the invoice being paid")


class CreatePayment(BaseModel):
    """
    Model for creating new payment transactions.
    
    This model handles the creation of instant payments with various payment methods
    and includes all necessary payment details and metadata.
    """
    invoice_id: int = Field(..., description="ID of the invoice being paid")
    merchantRefNum: Optional[str] = Field(None, description="Merchant reference number for tracking")
    amount: Optional[int] = Field(None, description="Payment amount in cents")
    currencyCode: Optional[str] = Field(None, description="Currency code (e.g., 'USD', 'EUR')")
    paymentHandleToken: Optional[str] = Field(None, description="Payment handle token for secure processing")
    card_number: Optional[str] = Field(None, description="Credit card number (if applicable)")
    data_descriptor: Optional[str] = Field(None, description="Data descriptor for secure payment data")
    data_value: Optional[str] = Field(None, description="Encrypted payment data value")
    payment_type: Optional[str] = Field(None, description="Type of payment method used")
    auth_pay_method: Optional[str] = Field(None, description="Authentication payment method")
    
    @validator("*", pre=True)
    def blank_strings(cls, value):
        """
        Validator to handle blank strings and zero values.
        
        Converts empty strings and zero values to None for cleaner data handling.
        """
        if isinstance(value, int):
            if value is None or value == 0:
                return None
        return value


class TransactionDetail(BaseModel):
    """
    Model for transaction detail information.
    
    This model represents key-value pairs that store additional transaction metadata
    and processing information.
    """
    key: str = Field(..., description="Detail key identifier")
    value: str = Field(..., description="Detail value content")

    @validator("*", pre=True)
    def blank_strings(cls, value):
        """
        Validator to clean up string values.
        
        Strips whitespace and converts empty strings to None.
        """
        if isinstance(value, str):
            value = value.strip()
            if value == "":
                return None
        return value


class Transaction(BaseModel):
    """
    Model representing a payment transaction.
    
    This model contains the core transaction information including status,
    amount, timestamps, and related entity IDs.
    """
    id: Optional[int] = Field(None, description="Unique transaction identifier")
    user_payment_method_id: Optional[int] = Field(None, description="ID of the user's payment method used")
    contact_payment_profile_id: Optional[int] = Field(None, description="ID of the contact payment profile used")
    status: Optional[str] = Field(None, description="Current transaction status")
    amount: Optional[float] = Field(None, description="Transaction amount")
    created_at: Optional[str] = Field(None, description="Transaction creation timestamp")
    update_at: Optional[str] = Field(None, description="Last update timestamp")


class RefundProcess(BaseModel):
    """
    Model for processing refunds.
    
    This model defines the structure for refunding transactions,
    including the payment method type and refund amount.
    """
    payment_method_type: Type = Field(default=Type.authnet, description="Payment method type for the refund")
    transaction_id: int = Field(gt=0, description="ID of the transaction to refund")
    amount: float = Field(gt=0, description="Refund amount (must be positive)")


class InvoiceItem(BaseModel):
    """
    Model for invoice items.
    
    This model represents individual items within an invoice that can be refunded.
    """
    id: int = Field(..., description="Invoice item identifier")
    quantity: int = Field(..., description="Quantity of the item")


class RefundInvoice(BaseModel):
    """
    Model for refunding invoice items.
    
    This model handles partial refunds by specifying which invoice items
    and services should be refunded and the total refund amount.
    """
    id: int = Field(..., description="Invoice identifier")
    invoice_items: Optional[List[InvoiceItem]] = Field(None, description="List of invoice items to refund")
    total_refund_amount: float = Field(..., description="Total amount to refund")
    invoice_service: Optional[List[InvoiceItem]] = Field(None, description="List of invoice services to refund")

    @validator("*", pre=True)
    def blank_strings(cls, value):
        """
        Validator to handle zero values in refund calculations.
        
        Converts zero values to None to avoid processing empty refunds.
        """
        if isinstance(value, int):
            value = abs(value)
            if value == 0:
                return None

        if isinstance(value, float):
            value = abs(value)
            if value == 0.0:
                return None
        return value


class RefundTransaction(BaseModel):
    """
    Model for refunding a transaction.
    
    This model combines transaction information with refund invoice details
    to process partial or full refunds.
    """
    transaction_id: int = Field(..., description="ID of the transaction to refund")
    refund_invoice: RefundInvoice = Field(..., description="Refund invoice details")
