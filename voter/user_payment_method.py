from sqlalchemy.orm import Session
from helper.interceptor import RequestHeaderValidatorInterceptor
from actions.utility_service import UtilityService
from sql.models.user_payment_methods import (
    UserPaymentMethods as UserPaymentMethodsModel,
)
from sql.models.payment_preference import PreferenceType

ADD = "add"
EDIT = "edit"
VIEW = "view"
SET_DEFAULT = "set_default"


class UserPaymentMethodVoter:
    def __init__(self):
        self.__interceptor = RequestHeaderValidatorInterceptor()
        self.__utility_service = UtilityService()

    def _default(self, db: Session, key, userPaymentMethod: UserPaymentMethodsModel):
        key_arr = [ADD, EDIT, VIEW, SET_DEFAULT]
        if key not in key_arr:
            return False
        if key == ADD:
            return self.__can_add(db, userPaymentMethod)
        if key == EDIT:
            return self.__can_edit(db, userPaymentMethod)
        if key == VIEW:
            return self.__can_view(db, userPaymentMethod)
        if key == SET_DEFAULT:
            return self.__can_set_default(db)
        return False

    def __can_view(self, db: Session, userPaymentMethod: UserPaymentMethodsModel):
        return self.__can_edit(db, userPaymentMethod)

    def __can_edit(self, db: Session, userPaymentMethod: UserPaymentMethodsModel):
        logged_in_user = self.__interceptor._get_logged_in_user()
        if logged_in_user:
            if userPaymentMethod is not None:
                if (
                    userPaymentMethod.payment_preference.user_id
                    == logged_in_user.id
                ):
                    return True
            else:
                return True

        return False

    def __can_add(self, db: Session, userPaymentMethod: UserPaymentMethodsModel):
        logged_in_user = self.__interceptor._get_logged_in_user()
        if logged_in_user:
            return True

        return False
    
    def __can_set_default(self, db: Session):
        logged_in_user = self.__interceptor._get_logged_in_user()
        if logged_in_user:
            return True
        return False