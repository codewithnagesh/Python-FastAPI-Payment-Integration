# This module defines the ContactPaymentProfileVoter class for authorization control
# in the payment API service. It implements permission checks for contact payment profile operations.

from sqlalchemy.orm import Session  # SQLAlchemy session for database operations
from helper.interceptor import RequestHeaderValidatorInterceptor  # Request validation interceptor
from actions.utility_service import UtilityService  # Utility service for payment operations
from sql.models.contact_payment_profile import (
    ContactPaymentProfile as ContactPaymentProfileModel,  # Contact payment profile model
)
from sql.models.payment_preference import PreferenceType  # Payment preference type enum

# Permission action constants
ADD = "add"    # Permission to add/create contact payment profiles
EDIT = "edit"  # Permission to edit/update contact payment profiles
VIEW = "view"  # Permission to view contact payment profiles


class ContactPaymentProfileVoter:
    """
    Voter class for contact payment profile authorization.
    
    This class implements permission checks for contact payment profile operations,
    ensuring users can only access and modify their own payment profiles.
    """
    
    def __init__(self):
        """
        Initializes the ContactPaymentProfileVoter with required dependencies.
        """
        self.__interceptor = RequestHeaderValidatorInterceptor()  # Request validation interceptor
        self.__utility_service = UtilityService()  # Utility service for payment operations

    def _default(
        self, db: Session, key, contactPaymentProfile: ContactPaymentProfileModel
    ):
        """
        Default permission check method for contact payment profile operations.
        
        Args:
            db (Session): Database session
            key (str): Permission action (add, edit, view)
            contactPaymentProfile (ContactPaymentProfileModel): Contact payment profile to check
            
        Returns:
            bool: True if permission is granted, False otherwise
        """
        key_arr = [ADD, EDIT, VIEW]  # Valid permission actions
        if key not in key_arr:
            return False
        if key == ADD:
            return self.__can_add(db, contactPaymentProfile)
        if key == EDIT:
            return self.__can_edit(db, contactPaymentProfile)
        if key == VIEW:
            return self.__can_view(db, contactPaymentProfile)

    def __can_view(
        self, db: Session, contactPaymentProfile: ContactPaymentProfileModel
    ):
        if isinstance(contactPaymentProfile, list):
            logged_in_user = self.__interceptor._get_logged_in_user()
            if logged_in_user:
                for item in contactPaymentProfile:
                    if (
                        item.user.id
                        == logged_in_user.id
                    ):
                        return True
            return False
        else:
            return self.__can_edit(db, contactPaymentProfile)

    def __can_edit(
        self, db: Session, contactPaymentProfile: ContactPaymentProfileModel
    ):
        logged_in_user = self.__interceptor._get_logged_in_user()
        if logged_in_user:
            if (
                contactPaymentProfile.user.id
                == logged_in_user.id
            ):
                return True

        return False

    def __can_add(self, db: Session, contactPaymentProfile: ContactPaymentProfileModel):
        logged_in_user = self.__interceptor._get_logged_in_user()
        if logged_in_user:
            return True

        return False
