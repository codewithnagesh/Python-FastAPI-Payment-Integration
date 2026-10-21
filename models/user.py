# This module defines Pydantic models for user-related operations in the payment API service.
# These models handle user authentication, profile updates, and timezone management.

from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field


class UserLogin(BaseModel):
    """
    Model for user login credentials.
    
    This model represents the data structure required for user authentication,
    including username, password, and optional remember me functionality.
    """
    username: str = Field(..., alias="_username", description="User's unique username")
    password: str = Field(..., alias="_password", description="User's password")
    rememberMe: bool = Field(..., description="Remember me option for persistent login")


class UserUpdatePassword(BaseModel):
    """
    Model for updating user password.
    
    This model is used when a user wants to change their password.
    """
    plain_password: str = Field(..., description="New plain text password")


class UserUpdate(BaseModel):
    """
    Model for updating user profile information.
    
    This model allows partial updates to user profile data including
    personal information, account status, and preferences.
    """
    id: int = Field(..., description="Unique user identifier")
    first_name: Optional[str] = Field(None, description="User's first name")
    last_name: Optional[str] = Field(None, description="User's last name")
    username: Optional[str] = Field(None, description="User's username")
    active: Optional[bool] = Field(None, description="User account active status")
    invoice_tax_rate: Optional[float] = Field(None, description="Tax rate for user invoices")
    timezone: Optional[str] = Field(None, description="User's timezone preference")
    

class UserPost(BaseModel):
    """
    Model for creating new users.
    
    This model defines the required and optional fields when creating a new user account.
    """
    first_name: Optional[str] = Field(None, description="User's first name")
    last_name: Optional[str] = Field(None, description="User's last name")
    plain_password: Optional[str] = Field(None, description="User's password in plain text")
    username: Optional[str] = Field(None, description="Unique username for the user")


class UserUpdateTimezone(BaseModel):
    """
    Model for updating user timezone.
    
    This model is specifically used for timezone updates to ensure
    proper time handling across different regions.
    """
    timezone: str = Field(..., description="User's timezone identifier (e.g., 'America/New_York')")

