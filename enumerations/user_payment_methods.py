# This module defines enumerations for user payment methods in the payment API service.
# These enums provide type-safe constants for payment method types and statuses.

from enum import Enum  # Base class for creating enumerations


class Type(str, Enum):
    """
    Enumeration of supported payment method types.
    
    This enum defines all the payment providers and methods supported by the system,
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
    Enumeration of payment method status types.
    
    This enum defines the possible states of a user's payment method during processing
    and approval workflows.
    """
    APPROVED = "approved"    # Payment method has been approved for use
    DECLINED = "declined"   # Payment method has been declined
    PENDING = "pending"    # Payment method is awaiting approval
    DISABLED = "disabled"   # Payment method has been disabled
