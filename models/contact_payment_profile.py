# This module defines Pydantic models for contact payment profile management in the payment API service.
# These models handle contact payment profiles, which are used for storing payment information
# associated with specific contacts or customers.

from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field


class UpdateContactPaymentProfile(BaseModel):
    """
    Model for updating contact payment profiles.
    
    This model handles updates to contact payment profiles, including
    user associations, profile IDs, and payment method references.
    """
    user_id: Optional[int] = Field(0, description="ID of the user associated with the profile")
    profile_id: Optional[int] = Field(0, description="ID of the payment profile to update")
    payment_profile_id: Optional[str] = Field(None, description="Payment processor's profile ID")
    reference_number: Optional[str] = Field(None, description="Reference number for the payment profile")
