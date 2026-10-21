# This module defines the PaymentPreferenceVoter class for authorization control
# in the payment API service. It implements permission checks for payment preference operations.

from sqlalchemy.orm import Session  # SQLAlchemy session for database operations
from helper.interceptor import RequestHeaderValidatorInterceptor  # Request validation interceptor
from actions.utility_service import UtilityService  # Utility service for payment operations
from sql.models.payment_preference import (
    PreferenceType,  # Payment preference type enum
    PaymentPreference as PaymentPreferenceModel,  # Payment preference model
)

# Permission action constants
ADD = "add"    # Permission to add/create payment preferences
EDIT = "edit"  # Permission to edit/update payment preferences
VIEW = "view"  # Permission to view payment preferences


class PaymentPreferenceVoter:
    """
    Voter class for payment preference authorization.
    
    This class implements permission checks for payment preference operations,
    ensuring users can only access and modify their own payment preferences.
    """
    
    def __init__(self):
        """
        Initializes the PaymentPreferenceVoter with required dependencies.
        """
        self.__interceptor = RequestHeaderValidatorInterceptor()  # Request validation interceptor
        self.__utility_service = UtilityService()  # Utility service for payment operations

    def _default(
        self, db: Session, key, paymentPreferenceModel: PaymentPreferenceModel
    ):
        """
        Default permission check method for payment preference operations.
        
        Args:
            db (Session): Database session
            key (str): Permission action (add, edit, view)
            paymentPreferenceModel (PaymentPreferenceModel): Payment preference to check
            
        Returns:
            bool: True if permission is granted, False otherwise
        """
        key_arr = [ADD, EDIT, VIEW]  # Valid permission actions
        if key not in key_arr:
            return False
        if key == ADD:
            return self.__can_add(db, paymentPreferenceModel)
        if key == EDIT:
            return self.__can_edit(db, paymentPreferenceModel)
        if key == VIEW:
            return self.__can_view(db, paymentPreferenceModel)

    def __can_view(self, db: Session, paymentPreferenceModel: PaymentPreferenceModel):
        if paymentPreferenceModel and paymentPreferenceModel.preference_type != "":
            if paymentPreferenceModel.preference_type == PreferenceType.USER:
                return True

        return False

    def __can_edit(self, db: Session, paymentPreferenceModel: PaymentPreferenceModel):
        logged_in_user = self.__interceptor._get_logged_in_user()
        if logged_in_user:
            return True

        return False

    def __can_add(self, db: Session, paymentPreferenceModel: PaymentPreferenceModel):
        logged_in_user = self.__interceptor._get_logged_in_user()
        if logged_in_user:
            return True

        return False
