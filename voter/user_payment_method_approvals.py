from sqlalchemy.orm import Session
from helper.interceptor import RequestHeaderValidatorInterceptor
from actions.utility_service import UtilityService
from sql.models.user_payment_method_approvals import (
    UserPaymentMethodApproval as UserPaymentMethodApprovalModel,
)

ADD = "add"
EDIT = "edit"
VIEW = "view"


class UserPaymentApprovalVoter:
    def __init__(self):
        self.__interceptor = RequestHeaderValidatorInterceptor()
        self.__utility_service = UtilityService()

    def _default(
        self,
        db: Session,
        key,
        userPaymentMethodApproval: UserPaymentMethodApprovalModel,
    ):
        key_arr = [ADD, EDIT, VIEW]
        if key not in key_arr:
            return False
        if key == ADD:
            return self.__can_add(db, userPaymentMethodApproval)
        if key == EDIT:
            return self.__can_edit(db, userPaymentMethodApproval)
        if key == VIEW:
            return self.__can_view(db, userPaymentMethodApproval)

    def __can_view(
        self, db: Session, userPaymentMethodApproval: UserPaymentMethodApprovalModel
    ):
        if userPaymentMethodApproval is None:
            return self.__can_edit(db, userPaymentMethodApproval)
        else:
            logged_in_user = self.__interceptor._get_logged_in_user()
            if logged_in_user:
                return True

    def __can_edit(
        self, db: Session, userPaymentMethodApproval: UserPaymentMethodApprovalModel
    ):
        logged_in_user = self.__interceptor._get_logged_in_user()
        if logged_in_user:
            return True

        return False

    def __can_add(
        self, db: Session, userPaymentMethodApproval: UserPaymentMethodApprovalModel
    ):
        logged_in_user = self.__interceptor._get_logged_in_user()
        if logged_in_user:
            return True

        return False
