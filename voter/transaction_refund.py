from sqlalchemy.orm import Session
from helper.interceptor import RequestHeaderValidatorInterceptor
from actions.utility_service import UtilityService
from sql.models.transaction_refunds import TransactionRefund as TransactionRefundModel

ADD = "add"
CANCEL = "cancel"
VIEW = "view"


class TransactionRefundVoter:
    def __init__(self):
        self.__interceptor = RequestHeaderValidatorInterceptor()

    def _default(self, db: Session, key, transaction_refund: TransactionRefundModel):
        key_arr = [ADD, CANCEL, VIEW]
        if key not in key_arr:
            return False
        if key == ADD:
            return self.__can_add(db)
        if key == CANCEL:
            return self.__can_cancel(db, transaction_refund)
        if key == VIEW:
            return self.__can_view(db, transaction_refund)

    def __can_cancel(self, db: Session, transaction_refund: TransactionRefundModel):
        logged_in_user = self.__interceptor._get_logged_in_user()
        if logged_in_user and transaction_refund:
            if transaction_refund.created_by == logged_in_user.id:
                return True
        return False

    def __can_view(self, db: Session, transaction_refund: TransactionRefundModel):
        return self.__can_cancel(db, transaction_refund)

    def __can_add(self, db: Session):
        logged_in_user = self.__interceptor._get_logged_in_user()
        if logged_in_user:
            return True
        return False
