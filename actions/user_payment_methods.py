from google.protobuf.json_format import MessageToDict
from marshmallow import EXCLUDE

# import base64, requests
# from decouple import config
from datetime import datetime
import proto.payments_proto.user_payment_methods.user_payment_methods_pb2
import proto.payments_proto.user_payment_methods.user_payment_methods_pb2_grpc
from helper.camel_to_snake import CamelToSnake
from helper.interceptor import RequestHeaderValidatorInterceptor
from sql.crud import (
    user as user_crud,
    user_payment_methods as user_payment_method_crud,
    user_payment_method_options as user_payment_method_option_crud,
    user_payment_method_approvals as user_payment_method_approval_crud,
    payment_preference as payment_preference_crud,
)
from enumerations.payment_preference import PreferenceType
from enumerations.user_payment_methods import StatusType, Type
from .paysafe.paysafe import PaysafeService
from .authnet.authnet import AuthnetService
from .utility_service import UtilityService
from voter.user_payment_method import UserPaymentMethodVoter
from actions.payment_preference import PaymentPreferenceService
from sql.schemas.user_payment_method_options import CreateUserPaymentMethodOptionSchema
from sql.schemas.user_payment_methods import (
    UserPaymentMethodSchema,
    CreateUserPaymentMethodSchema,
    UpdateUserPaymentMethodSchema,
    UpdateAuthnetUserPaymentMethodSchema,
)


class UserPaymentMethodService(
    proto.payments_proto.user_payment_methods.user_payment_methods_pb2_grpc.UserPaymentMethodsServiceServicer
):
    def __init__(self, db):
        self.__payment_preference_service = PaymentPreferenceService(db)
        self.__user_payment_method_schema = UserPaymentMethodSchema()
        self.__list_payment_method_schema = UserPaymentMethodSchema(many=True)
        self.__create_user_payment_method_schema = CreateUserPaymentMethodSchema()
        self.__create_user_payment_method_option_schema = (
            CreateUserPaymentMethodOptionSchema()
        )
        self.__update_user_payment_method_schema = UpdateUserPaymentMethodSchema()
        self.__update_authnet_user_payment_method_schema = (
            UpdateAuthnetUserPaymentMethodSchema()
        )
        self.__camel_to_snake = CamelToSnake()
        self.__interceptor = RequestHeaderValidatorInterceptor()
        self.__user_payment_method_voter = UserPaymentMethodVoter()
        self.__db = db
        # self.client = requests
        self.__paysafe_service = PaysafeService()
        self.__authnet_service = AuthnetService()
        self.__utility_service = UtilityService()

    def __del__(self):
        self.__db.close()

    def _approved_payment_method(self, logged_in_user, payment_method_type):
        is_active_preference = self.__payment_preference_service._active_preference(
            logged_in_user.id, payment_method_type
        )

        if is_active_preference and is_active_preference is not None:
            user_id = None
            if is_active_preference.preference_type == PreferenceType.USER:
                user_id = logged_in_user.id
            import logging

            logging.error(user_id)
            logging.error(payment_method_type)
            approved_payment_method = (
                user_payment_method_crud._get_approved_payment_method(
                    self.__db,
                    user_id,
                    payment_method_type,
                )
            )
            if approved_payment_method and approved_payment_method is not None:
                return approved_payment_method
            else:
                raise PermissionError(f"User not have any active payment method!")

    def _getValueByKeyForArray(self, key, items):
        for item in items:
            if item.key == key:
                return item.value
        return None

    # Create call
    def CreateUserPaymentMethod(self, request, context):
        try:
            data = self.__camel_to_snake._decode_keys(
                MessageToDict(request.user_payment_method_data)
            )

            if not self.__user_payment_method_voter._default(self.__db, "add", None):
                raise PermissionError("Access denied!")

            logged_in_user = self.__interceptor._get_logged_in_user()
            preference = self.__payment_preference_service._active_preference(
                logged_in_user.id, data["payment_method_type"]
            )

            data["user_id"] = None
            if preference.preference_type == PreferenceType.USER:
                data["user_id"] = logged_in_user.id

            check_payment_method = (
                user_payment_method_crud._get_approved_pending_payment_method(
                    self.__db,
                    data["user_id"],
                    data["payment_method_type"],
                )
            )

            if check_payment_method:
                raise PermissionError(
                    "You already have a "
                    + check_payment_method.payment_method_type.upper()
                    + " payment method with "
                    + check_payment_method.status.upper()
                    + " status."
                )

            data["payment_preference_id"] = preference.id
            data["created_by"] = logged_in_user.id
            data["status"] = StatusType.PENDING
            result = self.__create_user_payment_method_schema.load(
                data, session=self.__db, unknown=EXCLUDE
            )
            user_payment_method = user_payment_method_crud._create(self.__db, result)
            if user_payment_method:
                payment_method_option = {}
                for key, value in data.items():
                    if key == "application_number":
                        payment_method_option = {"key": key, "value": str(value)}

                payment_method_option["user_payment_method_id"] = user_payment_method.id
                result_up = self.__create_user_payment_method_option_schema.load(
                    payment_method_option, session=self.__db, unknown=EXCLUDE
                )
                user_payment_method_option_crud._create(self.__db, result_up)

                self.__db.close()
                return proto.payments_proto.user_payment_methods.user_payment_methods_pb2.CreateUserPaymentMethodResponse(
                    message=f"Payment method ({data['payment_method_type'].upper()}) has been successfully added."
                )
            else:
                self.__db.close()
                raise PermissionError("Failed to create user payment method!")

        except Exception as e:
            self.__del__()
            raise PermissionError(str(e))

    def ReadUserCurrentPaymentMethod(self, request, context):
        try:
            logged_in_user = self.__interceptor._get_logged_in_user()

            # TODO: check if user exists and has permission to add preference for the given user
            if request.user_id is not None and request.user_id > 0:
                logged_in_user = user_crud.get_user(self.__db, request.user_id)
                if logged_in_user is None:
                    raise PermissionError("User not found!")
            
            user_id = None
            if (
                request.preference == PreferenceType.USER
                and logged_in_user.id == request.id
            ):
                user_id = logged_in_user.id
            else:
                raise PermissionError("Please provide valid details.")

            user_payment_method = (
                user_payment_method_crud._get_approved_pending_payment_method(
                    self.__db,
                    user_id,
                    request.payment_method_type,
                )
            )

            if not self.__user_payment_method_voter._default(
                self.__db, "view", user_payment_method
            ):
                raise PermissionError("Access denied!")

            result = self.__user_payment_method_schema.dump(user_payment_method)
            
            for option in result['payment_method_options']:
                if option["key"] in [
                    "auth_login_id",
                    "auth_transaction_key",
                    "auth_client_key",
                ]:
                    new_value = self.__authnet_service.GetSecureAuthAccess(
                        option["key"], option["value"]
                    )
                    option["value"] = new_value
            
            
            self.__db.close()
            return proto.payments_proto.user_payment_methods.user_payment_methods_pb2.ReadUserCurrentPaymentMethodResponse(
                user_payment_method_data=result
            )

        except Exception as e:
            self.__del__()
            raise PermissionError(str(e))

    def _active_payment_methods(self, logged_in_user, payment_method_type, is_default, get_all: bool = False):
        is_active_preferences = payment_preference_crud._get_by_user(
            self.__db, logged_in_user.id
        )
        approved_payment_methods = []
        for is_active_preference in is_active_preferences:
            if is_active_preference:
                payment_methods = user_payment_method_crud._get_user_active_payment_method_by_preferece(
                    self.__db, is_active_preference.id, payment_method_type, is_default
                )

                if len(payment_methods) > 0:
                    for payment_method in payment_methods:
                        if payment_method:
                            if get_all:
                                approved_payment_methods.append(payment_method)
                            else:
                                if (
                                    is_active_preference.preference_type
                                    == PreferenceType.USER
                                    and payment_method.user_id == logged_in_user.id
                                ):
                                    approved_payment_methods.append(payment_method)
                                else:
                                    if payment_method.payment_method_type == Type.AUTHNET:
                                        approved_payment_methods.append(payment_method)

        return approved_payment_methods

    #  Get Payment Method By User ID {Public}
    def ReadUserActivePaymentMethod(self, request, context):
        try:
            user = user_crud.get_user(self.__db, request.user_id)
            if not user:
                raise PermissionError("Please provide valid user details!")

            payment_methods = self._active_payment_methods(
                user, request.payment_method_type, request.is_default
            )
            active_payment_methods = []
            for payment_method in payment_methods:
                if payment_method and payment_method.payment_method_options:
                    account_number = self._getValueByKeyForArray(
                        "account_number", payment_method.payment_method_options
                    )
                    account_name = self._getValueByKeyForArray(
                        "account_name", payment_method.payment_method_options
                    )
                    account_currency = self._getValueByKeyForArray(
                        "account_currency", payment_method.payment_method_options
                    )
                    merchant_id = self._getValueByKeyForArray(
                        "merchant_id", payment_method.payment_method_options
                    )
                    auth_login_id = self._getValueByKeyForArray(
                        "auth_login_id", payment_method.payment_method_options
                    )
                    auth_transaction_key = self._getValueByKeyForArray(
                        "auth_transaction_key", payment_method.payment_method_options
                    )
                    auth_client_key = self._getValueByKeyForArray(
                        "auth_client_key", payment_method.payment_method_options
                    )
                    active_payment_methods.append(
                        {
                            "id": payment_method.id,
                            "user_id": payment_method.user_id,
                            "payment_method_type": payment_method.payment_method_type,
                            "auth_login_id": auth_login_id,
                            "auth_transaction_key": auth_transaction_key,
                            "auth_client_key": auth_client_key,
                            "account_number": account_number,
                            "account_name": account_name,
                            "account_currency": account_currency,
                            "merchant_id": merchant_id,
                            "is_default_payment_method": payment_method.is_default,
                        }
                    )
            return proto.payments_proto.user_payment_methods.user_payment_methods_pb2.ReadUserActivePaymentMethodResponse(
                response=active_payment_methods
            )
        except Exception as e:
            self.__del__()
            raise PermissionError(str(e))

    # Update Call
    def UpdateUserPaymentMethod(self, request, context):
        try:
            data = self.__camel_to_snake._decode_keys(
                MessageToDict(request.user_payment_method_data)
            )

            logged_in_user = self.__interceptor._get_logged_in_user()
            self.__payment_preference_service._active_preference(
                logged_in_user.id, data["payment_method_type"]
            )

            approval = user_payment_method_approval_crud._check_approval_by_user(self.__db, logged_in_user.id, data["payment_method_type"])
            if not approval:
                raise PermissionError(f"{data['payment_method_type']} type payment method is not approved by this user")
            
            record = user_payment_method_crud._get_by_id(self.__db, request.id)
            if not record:
                raise FileNotFoundError("Record not found!")

            if record.status == StatusType.APPROVED:
                raise PermissionError("Payment method is already approved!")

            if not self.__user_payment_method_voter._default(self.__db, "edit", record):
                raise PermissionError("Access denied!")

            is_account_number_valid = self.__checkAccountIdFromPaysafe(
                data["account_currency"], data["account_number"]
            )
            if is_account_number_valid is False:
                raise PermissionError("Please provide the valid accound number.")

            data["status"] = "approved"
            data["updated_by"] = logged_in_user.id
            data["is_default"] = approval.is_default
            result = self.__update_user_payment_method_schema.load(
                data, session=self.__db, unknown=EXCLUDE
            )
            user_payment_method = user_payment_method_crud._update(
                self.__db, record, result
            )
            
            payment_method_options = []
            for key, value in data.items():
                if (
                    key != "payment_method_type"
                    and key != "status"
                    and key != "created_by"
                ):
                    payment_method_options.append({"key": key, "value": str(value)})

            for payment_method_option in payment_method_options:
                payment_method_option["user_payment_method_id"] = user_payment_method.id
                result_up = self.__create_user_payment_method_option_schema.load(
                    payment_method_option, session=self.__db, unknown=EXCLUDE
                )
                user_payment_method_option_crud._create(self.__db, result_up)

            response = self.__user_payment_method_schema.dump(user_payment_method)
            self.__db.close()

            return proto.payments_proto.user_payment_methods.user_payment_methods_pb2.UpdateUserPaymentMethodResponse(
                user_payment_method_data=response
            )
        except Exception as e:
            self.__del__()
            raise PermissionError(e)

    def __checkAccountIdFromPaysafe(self, USD, account_number):
        try:
            response = self.__paysafe_service.FindPaymentMethods(USD)
            payment_response = response.json()
            if not response.status_code in [200, 201]:
                data = response.json()
                error_message = data["error"]["message"]
                error_code = data["error"]["code"]
                raise PermissionError(error_code + ": " + error_message)

            payment_methods = payment_response["paymentMethods"]

            accountId = []
            for method in payment_methods:
                accountId.append(method["accountId"])

            if account_number in accountId:
                return True

            return False
        except Exception as e:
            self.__del__()
            raise PermissionError(e)

    # Soft Delete Call
    def SoftDeleteUserPaymentMethod(self, request, context):
        try:
            logged_in_user = self.__interceptor._get_logged_in_user()

            record = user_payment_method_crud._get_by_id(self.__db, request.id)
            if not record:
                raise PermissionError(
                    f"User payment method is not available in the database on id = {request.id}"
                )

            if not self.__user_payment_method_voter._default(self.__db, "edit", record):
                raise PermissionError("Access denied!")

            user_payment_method_crud._soft_delete(self.__db, record, logged_in_user)

            self.__db.close()
            return proto.payments_proto.user_payment_methods.user_payment_methods_pb2.SoftDeleteUserPaymentMethodResponse(
                success=True
            )

        except Exception as e:
            raise PermissionError(e)

    def StoreAuthorizenetAuthAccess(self, request, context):
        try:
            logged_in_user = self.__interceptor._get_logged_in_user()
            if logged_in_user:
                raise PermissionError("Access denied!")

            user = user_crud.get_user(self.__db, request.user_id)
            if user.id != request.user_id:
                raise PermissionError(
                    "Please provide correct user details!"
                )

            approval = user_payment_method_approval_crud._check_approval_by_user(self.__db, logged_in_user.id, request.payment_method_type)
            if not approval:
                raise PermissionError(f"{request.payment_method_type} type payment method is not approved by this user")

            preference = self.__payment_preference_service._active_preference(
                user.id, request.payment_method_type
            )

            data = {}
            data["user_id"] = None
            data["payment_method_type"] = request.payment_method_type
            data["is_default"] = approval.is_default
            if preference.preference_type == PreferenceType.USER:
                data["user_id"] = user.id
            else:
                raise PermissionError(
                    "You cannot access this resource because you are not a right user."
                )

            check_payment_method = (
                user_payment_method_crud._get_approved_pending_payment_method(
                    self.__db,
                    data["user_id"],
                    data["payment_method_type"],
                )
            )

            if check_payment_method:
                raise PermissionError(
                    "You already have a "
                    + check_payment_method.status.upper()
                    + " payment method."
                )

            data["payment_preference_id"] = preference.id
            data["created_by"] = logged_in_user.id
            data["status"] = StatusType.APPROVED

            result = self.__create_user_payment_method_schema.load(
                data, session=self.__db, unknown=EXCLUDE
            )
            user_payment_method = user_payment_method_crud._create(self.__db, result)

            option_data = self.__authnet_service.SetSecureAuthAccess(
                {
                    "auth_login_id": request.auth_login_id,
                    "auth_transaction_key": request.auth_transaction_key,
                    "auth_client_key": request.auth_client_key,
                }
            )

            if user_payment_method:
                payment_method_option = {}
                for key, value in option_data.items():
                    payment_method_option = {"key": key, "value": str(value)}

                    payment_method_option["user_payment_method_id"] = (
                        user_payment_method.id
                    )
                    result_up = self.__create_user_payment_method_option_schema.load(
                        payment_method_option, session=self.__db, unknown=EXCLUDE
                    )
                    user_payment_method_option_crud._create(self.__db, result_up)

                self.__db.close()
                return proto.payments_proto.user_payment_methods.user_payment_methods_pb2.StoreAuthorizenetAuthAccessResponse(
                    message=f"Payment method {data['payment_method_type'].upper()} has been successfully added."
                )
            else:
                self.__db.close()
                raise PermissionError("Failed to create user payment method!")

        except Exception as e:
            self.__del__()
            raise PermissionError(str(e))

    def UpdateAuthorizenetAuthAccess(self, request, context):
        try:
            logged_in_user = self.__interceptor._get_logged_in_user()
            if logged_in_user:
                raise PermissionError("Access denied!")

            user = user_crud.get_user(self.__db, request.user_id)
            if user.id != request.user_id:
                raise PermissionError(
                    "Please provide correct user details!"
                )

            preference = self.__payment_preference_service._active_preference(
                user.id, request.payment_method_type
            )

            data = {}
            data["user_id"] = None
            data["payment_method_type"] = request.payment_method_type
            if preference.preference_type == PreferenceType.USER:
                data["user_id"] = user.id

            record = user_payment_method_crud._get_approved_pending_payment_method(
                self.__db,
                data["user_id"],
                data["payment_method_type"],
            )

            if not record:
                raise PermissionError("This user has no payment method.")

            data["payment_preference_id"] = preference.id
            data["updated_by"] = logged_in_user.id
            data["status"] = StatusType.APPROVED

            result = self.__update_authnet_user_payment_method_schema.load(
                data, session=self.__db, unknown=EXCLUDE
            )
            user_payment_method = user_payment_method_crud._update(
                self.__db, record, result
            )

            user_payment_method_option_crud._delete(self.__db, user_payment_method.id)

            option_data = self.__authnet_service.SetSecureAuthAccess(
                {
                    "auth_login_id": request.auth_login_id,
                    "auth_transaction_key": request.auth_transaction_key,
                    "auth_client_key": request.auth_client_key,
                }
            )

            if user_payment_method:
                payment_method_option = {}
                for key, value in option_data.items():
                    payment_method_option = {"key": key, "value": str(value)}

                    payment_method_option["user_payment_method_id"] = (
                        user_payment_method.id
                    )
                    result_up = self.__create_user_payment_method_option_schema.load(
                        payment_method_option, session=self.__db, unknown=EXCLUDE
                    )
                    user_payment_method_option_crud._create(self.__db, result_up)

                self.__db.close()
                return proto.payments_proto.user_payment_methods.user_payment_methods_pb2.UpdateAuthorizenetAuthAccessResponse(
                    message=f"Payment method {data['payment_method_type'].upper()} has been successfully updated."
                )
            else:
                self.__db.close()
                raise PermissionError("Failed to create user payment method!")

        except Exception as e:
            self.__del__()
            raise PermissionError(str(e))

    def ListUserPaymentMethods(self, request, context):
        try:
            user_id = request.user_id
            payment_preference_id = request.payment_preference_id
            logged_in_user = self.__interceptor._get_logged_in_user()

            if logged_in_user:
                raise PermissionError("Access denied!")

            start_date = None
            if hasattr(request, "start_date"):
                if request.start_date != "":
                    start_date = datetime.strptime(request.start_date, "%Y-%m-%d")
            end_date = None
            if hasattr(request, "end_date"):
                if request.end_date != "":
                    end_date = datetime.strptime(request.end_date, "%Y-%m-%d")

            list = user_payment_method_crud._list_user_payment_methods(
                self.__db,
                filter=request.filter,
                order_by=request.order_by,
                status=request.status,
                order_direction=request.order_direction,
                payment_method_type=request.payment_method_type,
                user_id=user_id,
                payment_preference_id=payment_preference_id,
                start_date=start_date,
                end_date=end_date,
                page=request.page,
                limit=request.limit,
            )

            user_payment_methods_list = self.__list_payment_method_schema.dump(
                list["payment_methods"]
            )

            for user_payment_methods in user_payment_methods_list:

                payment_method_options = user_payment_methods.get(
                    "payment_method_options", []
                )

                for option in payment_method_options:
                    if option["key"] in [
                        "auth_login_id",
                        "auth_transaction_key",
                        "auth_client_key",
                    ]:
                        new_value = self.__authnet_service.GetSecureAuthAccess(
                            option["key"], option["value"]
                        )
                        option["value"] = new_value

            meta = {
                "page": list["page"],
                "limit": list["limit"],
                "current_items": list["items"],
                "total_items": list["total_items"],
            }
            self.__db.close()
            return proto.payments_proto.user_payment_methods.user_payment_methods_pb2.ListUserPaymentMethodsResponse(
                meta=meta, user_payment_methods=user_payment_methods_list
            )
        except Exception as e:
            self.__del__()
            raise PermissionError(str(e))

    def get_value_for_key(self, payment_method_options, key):
        for option in payment_method_options:
            if option == str(key):
                return option["value"]
        return None  # if the key is not found

    def SetDefaultPaymentMethod(self, request, context):
        try:
            logged_in_user = self.__interceptor._get_logged_in_user()
            requesting_user = logged_in_user

            if not self.__user_payment_method_voter._default(self.__db, "set_default", None):
                raise PermissionError("Access denied.")

            if request.user_id and request.user_id > 0:
                if not logged_in_user:
                    raise PermissionError("Please provide valid user details.")
            
            check_approval = user_payment_method_approval_crud._check_approval_by_user(self.__db, logged_in_user.id, request.payment_method)
            if not check_approval:
                raise PermissionError(f"{request.payment_method} type payment approval is not available for this user.")

            validate_payment_method = self._active_payment_methods(logged_in_user, check_approval.payment_method_type, None, True)

            all_payment_method = self._active_payment_methods(logged_in_user, None, None, True)
            for payment_method in all_payment_method:
                if payment_method and payment_method is not None:
                    user_payment_method_crud.set_default_payment_method(self.__db, payment_method, False, requesting_user.id)

            for payment_method in validate_payment_method:
                if payment_method and payment_method is not None:
                    user_payment_method_crud.set_default_payment_method(self.__db, payment_method, True, requesting_user.id)
            
            approvals = user_payment_method_approval_crud._get_approvals_by_user(self.__db, logged_in_user.id)
            for approval in approvals:
                if approval:
                    user_payment_method_approval_crud._set_default(self.__db, approval, False)

            user_payment_method_approval_crud._set_default(self.__db, check_approval, True)
            self.__db.close()
            return proto.payments_proto.user_payment_methods.user_payment_methods_pb2.SetDefaultPaymentMethodResponse(
                message=f"{request.payment_method} default payment method has been set successfully."
            )
        except Exception as e:
            self.__del__()
            raise PermissionError(str(e))
