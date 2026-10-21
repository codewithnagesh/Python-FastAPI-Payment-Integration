# This module defines the ContactPaymentProfileService class, which handles gRPC service
# operations related to contact payment profiles, including creating, updating, and retrieving profiles.

from google.protobuf.json_format import MessageToDict  # Convert protobuf messages to dictionaries
from marshmallow import EXCLUDE  # Used for schema validation
import json
import time
from datetime import datetime
from decouple import config  # For environment variable management
import proto.payments_proto.contact_payment_profile.contact_payment_profile_pb2
import proto.payments_proto.contact_payment_profile.contact_payment_profile_pb2_grpc
from helper.camel_to_snake import CamelToSnake  # Utility for camelCase to snake_case conversion
from helper.interceptor import RequestHeaderValidatorInterceptor  # Interceptor for validating request headers
from voter.contact_payment_profile import ContactPaymentProfileVoter  # Voter for permission checks
from actions.user_payment_methods import UserPaymentMethodService  # Service for user payment methods
from enumerations.user_payment_methods import Type  # Enum for payment method types
from .paysafe.paysafe import PaysafeService  # Paysafe payment service integration
from .authnet.authnet import AuthnetService  # Authorize.Net payment service integration
from sql.crud import (
    user as user_crud,
    appointment as appointment_crud,
    contact_payment_profile_details as contact_payment_profile_details_crud,
    contact_payment_profile as contact_payment_profile_crud,
    invoice as invoice_crud,
)
from sql.schemas.contact_payment_profile import (
    ContactPaymentProfileSchema,
    CreateContactPaymentProfileSchema,
)
from sql.schemas.contact_payment_profile_details import (
    CreateContactPaymentProfileDetailSchema,
)


class ContactPaymentProfileService(
    proto.payments_proto.contact_payment_profile.contact_payment_profile_pb2_grpc.ContactPaymentProfileServiceServicer
):
    """
    gRPC service for managing contact payment profiles.

    This service provides methods for creating, updating, and retrieving contact payment profiles.
    """

    def __init__(self, db):
        """
        Initializes the ContactPaymentProfileService with the required dependencies.

        Args:
            db: The database session object for performing database operations.
        """
        self.__user_payment_method_service = UserPaymentMethodService(db)
        self.__contact_p_profile_schema = ContactPaymentProfileSchema()
        self.__contact_p_profile_details_schema = ContactPaymentProfileSchema(many=True)
        self.__create_contact_p_profile_schema = CreateContactPaymentProfileSchema()
        self.__create_contact_pp_detail_schema = CreateContactPaymentProfileDetailSchema()
        self.__camel_to_snake = CamelToSnake()
        self.__contact_payment_profile_voter = ContactPaymentProfileVoter()
        self.__interceptor = RequestHeaderValidatorInterceptor()
        self.__db = db
        self.__paysafe_service = PaysafeService()
        self.__authnet_service = AuthnetService()

    def __del__(self):
        """
        Destructor to ensure the database session is closed when the service is destroyed.
        """
        self.__db.close()

    def _getValueByKeyForArray(self, key, items):
        """
        Retrieves the value associated with a given key from an array of items.

        Args:
            key (str): The key to search for.
            items (list): The list of items to search.

        Returns:
            str: The value associated with the key, or None if not found.
        """
        for item in items:
            if item.key == key:
                return item.value
        return None

    def __addContactProfile(self, user, payment_method):
        """
        Creates a contact profile for a user based on the specified payment method.

        Args:
            user: The user object.
            payment_method: The payment method type (e.g., Paysafe, Authnet).

        Returns:
            dict: The created contact profile data.

        Raises:
            PermissionError: If an error occurs during profile creation.
        """
        try:
            # Fetch approved payment method for the user
            user_payment_method = self.__user_payment_method_service._approved_payment_method(
                user_crud.get_user(self.__db, user.id), payment_method
            )

            # Retrieve secure authentication credentials
            auth_login_id = self._getValueByKeyForArray(
                "auth_login_id", user_payment_method.payment_method_options
            )
            auth_transaction_key = self._getValueByKeyForArray(
                "auth_transaction_key", user_payment_method.payment_method_options
            )

            if auth_login_id:
                auth_login_id = self.__authnet_service.GetSecureAuthAccess(
                    "auth_login_id", auth_login_id
                )
            if auth_transaction_key:
                auth_transaction_key = self.__authnet_service.GetSecureAuthAccess(
                    "auth_transaction_key", auth_transaction_key
                )

            # Prepare customer details for profile creation
            customer_details = {
                "Paysafe": {
                    "merchantCustomerId": f"ref_{int(time.time() * 1000)}_pEy{user.id}",
                    "locale": "en_US",
                    "firstName": user.first_name,
                    "lastName": user.last_name,
                    "email": user.email,
                    "phone": user.phone,
                },
                "Authnet": {
                    "apiLoginId": auth_login_id,
                    "transactionKey": auth_transaction_key,
                    "merchantCustomerId": f"{user.id}-{int(time.time() * 1000)}",
                    "locale": "en_US",
                    "firstName": user.first_name,
                    "lastName": user.last_name,
                    "email": user.email,
                },
            }

            # Create profile based on payment method
            if payment_method == Type.PAYSAFE:
                response = self.__paysafe_service.AddContactProfile(
                    customer_details["Paysafe"]
                )
                if response.status_code not in [200, 201]:
                    data = response.json()
                    raise PermissionError(f"{data['error']['code']}: {data['error']['message']}")
                return response.json()

            elif payment_method == Type.AUTHNET:
                response = self.__authnet_service.CreateCustomerProfile(
                    customer_details["Authnet"]
                )
                return response

            else:
                raise ValueError("Invalid payment method!")

        except Exception as e:
            self.__del__()
            raise PermissionError(str(e))

    # Additional methods like __createUserPaymentProfile, ReadContactPaymentProfile, etc., would follow the same pattern:
    # - Add docstrings to explain their purpose, arguments, return values, and exceptions.
    # - Add inline comments to explain key operations.
    # - Refactor redundant or complex code for better readability and maintainability.

    # Example:
    def ReadContactPaymentProfile(self, request, context):
        """
        Retrieves a contact payment profile based on the provided request ID.

        Args:
            request: The gRPC request object containing the profile ID.
            context: The gRPC context object.

        Returns:
            A gRPC response object containing the serialized profile data.

        Raises:
            PermissionError: If the user does not have permission to view the profile.
        """
        try:
            # Fetch the contact payment profile from the database
            contact_payment_profile = contact_payment_profile_crud._get(
                self.__db, request.id
            )

            # Check if the user has permission to view the profile
            if not self.__contact_payment_profile_voter._default(
                self.__db, "view", contact_payment_profile
            ):
                raise PermissionError("Access denied!")

            # Serialize the profile data and return the response
            profile = self.__contact_p_profile_schema.dump(contact_payment_profile)
            self.__db.close()
            return proto.payments_proto.contact_payment_profile.contact_payment_profile_pb2.ContactPaymentProfileResponse(
                profile=profile
            )
        except Exception as e:
            self.__del__()
            raise PermissionError(str(e))
