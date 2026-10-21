# This module defines the TransactionVoter class for authorization control
# in the payment API service. It implements permission checks for transaction operations.

from sqlalchemy.orm import Session  # SQLAlchemy session for database operations
from helper.interceptor import RequestHeaderValidatorInterceptor  # Request validation interceptor
from actions.utility_service import UtilityService  # Utility service for payment operations
from sql.models.transactions import Transactions as TransactionsModel  # Transactions model

# Permission action constants
ADD = "add"    # Permission to add/create transactions
EDIT = "edit"  # Permission to edit/update transactions
VIEW = "view"  # Permission to view transactions


class TransactionVoter:
    """
    Voter class for transaction authorization.
    
    This class implements permission checks for transaction operations,
    ensuring users can only access and modify their own transactions.
    """
    
    def __init__(self):
        """
        Initializes the TransactionVoter with required dependencies.
        """
        self.__interceptor = RequestHeaderValidatorInterceptor()  # Request validation interceptor
        self.__utility_service = UtilityService()  # Utility service for payment operations

    def _default(self, db: Session, key, transactions: TransactionsModel):
        """
        Default permission check method for transaction operations.
        
        Args:
            db (Session): Database session
            key (str): Permission action (add, edit, view)
            transactions (TransactionsModel): Transaction to check
            
        Returns:
            bool: True if permission is granted, False otherwise
        """
        key_arr = [ADD, EDIT, VIEW]  # Valid permission actions
        if key not in key_arr:
            return False
        if key == ADD:
            return self.__can_add(db, transactions)
        if key == EDIT:
            return self.__can_edit(db, transactions)
        if key == VIEW:
            return self.__can_view(db, transactions)

    def __can_view(self, db: Session, transactions: TransactionsModel):
        return self.__can_edit(db, transactions)

    def __can_edit(self, db: Session, transactions: TransactionsModel):
        logged_in_user = self.__interceptor._get_logged_in_user()
        if logged_in_user:
            if transactions.user.id == logged_in_user.id:
                return True

        return False

    def __can_add(self, db: Session, transactions: TransactionsModel):
        logged_in_user = self.__interceptor._get_logged_in_user()
        if logged_in_user:
            return True

        return False
