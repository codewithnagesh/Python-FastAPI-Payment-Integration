# This module defines enumerations for payment preferences in the payment API service.
# These enums provide type-safe constants for payment preference types and statuses.

from enum import Enum  # Base class for creating enumerations


class PreferenceType(str, Enum):
    """
    Enumeration of payment preference types.
    
    This enum defines the different types of payment preferences that can be set
    for users, determining the scope and behavior of payment method preferences.
    """
    USER = "user"  # User-level payment preferences

    def __str__(self):
        """
        String representation of the enum value.
        
        Returns:
            str: The string value of the enum
        """
        return str(self.value)
