# This module defines enumerations for user payment method approvals in the payment API service.
# These enums provide type-safe constants for payment method types and approval statuses.

from enum import Enum  # Base class for creating enumerations


class PaymentType(str, Enum):
    """
    Enumeration of supported payment method types for approvals.
    
    This enum defines all the payment providers that can be approved for users,
    including traditional payment processors and modern digital wallets.
    """
    AUTHNET = "authnet"      # Authorize.Net payment processor
    PAYSAFE = "paysafe"      # Paysafe payment processor
    JUPITER = "jupiter"      # Jupiter payment processor
    STRIPE = "stripe"        # Stripe payment processor
    PAYPAL = "paypal"        # PayPal payment processor
    GOOGLEPAY = "googlepay"  # Google Pay digital wallet
    APPLEPAY = "applepay"    # Apple Pay digital wallet


class StatusType(str, Enum):
    """
    Enumeration of payment method approval status types.
    
    This enum defines the possible states of a payment method approval request
    during the approval workflow process.
    """
    APPROVED = "approved"     # Payment method approval has been approved
    DECLINED = "declined"     # Payment method approval has been declined
    PENDING = "pending"      # Payment method approval is awaiting review
    INPROGRESS = "inprogress" # Payment method approval is currently being processed
