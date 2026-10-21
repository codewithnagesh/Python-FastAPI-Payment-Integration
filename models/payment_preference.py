# This module defines Pydantic models for payment preference management in the payment API service.
# These models handle user payment preferences and payment method type configurations.

from __future__ import annotations
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class PreferenceType(str, Enum):
    """
    Enumeration of preference types.
    
    Defines the scope of payment preferences (user-level, system-level, etc.).
    """
    USER = "user"  # User-level preferences


class Type(str, Enum):
    """
    Enumeration of supported payment method types for preferences.
    
    This enum defines all the payment providers that can be set as preferences.
    """
    authnet = "authnet"      # Authorize.Net payment processor
    paysafe = "paysafe"      # Paysafe payment processor
    jupiter = "jupiter"       # Jupiter payment processor
    stripe = "stripe"        # Stripe payment processor
    paypal = "paypal"         # PayPal payment processor
    googlepay = "googlepay"  # Google Pay digital wallet
    applepay = "applepay"    # Apple Pay digital wallet


class AddPreference(BaseModel):
    """
    Model for adding new payment preferences.
    
    This model is used to set user payment method preferences,
    allowing users to specify their preferred payment processor.
    """
    preference_type: PreferenceType = Field(default=PreferenceType.USER, description="Type of preference being set")
    payment_method_type: Type = Field(default=Type.authnet, description="Preferred payment method type")
    user_id: Optional[int] = Field(None, description="ID of the user setting the preference")


class ChangePreferenceType(BaseModel):
    """
    Model for changing payment preference types.
    
    This model allows users to update their payment method preferences
    by changing the preferred payment processor.
    """
    preference_type: PreferenceType = Field(default=PreferenceType.USER, description="Type of preference to change")
    payment_method_type: Type = Field(default=Type.authnet, description="New preferred payment method type")
