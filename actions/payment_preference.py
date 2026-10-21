# This module defines the PaymentPreferenceService class, which handles gRPC service
# operations related to payment preferences, including creating, updating, and retrieving preferences.

from google.protobuf.json_format import MessageToDict  # Used for converting protobuf messages to dictionaries
from marshmallow import EXCLUDE
from helper.camel_to_snake import CamelToSnake  # Utility for converting camelCase to snake_case
from helper.interceptor import RequestHeaderValidatorInterceptor  # Interceptor for validating request headers
import proto.payments_proto.payment_preference.payment_preference_pb2  # Protobuf definitions for payment preferences
import proto.payments_proto.payment_preference.payment_preference_pb2_grpc  # gRPC service definitions for payment preferences
from voter.payment_preference import PaymentPreferenceVoter  # Voter for permission checks
import sql.crud.user as user_crud
import sql.crud.payment_preference as payment_preference_crud  # CRUD operations for payment preferences
import sql.crud.user_payment_methods as user_payment_methods_crud
import sql.crud.user_payment_method_approvals as user_payment_method_approval_crud
from actions.user_payment_method_approvals import UserPaymentMethodApprovalService  # Service for user payment method approvals
from sql.schemas.payment_preference import (  # Schemas for validating and serializing payment preference data
    PaymentPreferenceSchema,
    UpdatePaymentPreferenceSchema,
    CreatePaymentPreferenceSchema,
)


class PaymentPreferenceService(
    proto.payments_proto.payment_preference.payment_preference_pb2_grpc.PaymentPreferenceServiceServicer
):
    """
    gRPC service for managing payment preferences.

    This service provides methods for creating, updating, and retrieving payment preferences.
    """

    def __init__(self, db):
        """
        Initializes the PaymentPreferenceService with the required dependencies.

        Args:
            db: The database session object for performing database operations.
        """
        self.__camel_to_snake = CamelToSnake()  # Utility for camelCase to snake_case conversion
        self.__user_payment_method_approval = UserPaymentMethodApprovalService(db)  # Service for payment method approvals
        self.__interceptor = RequestHeaderValidatorInterceptor()  # Interceptor for validating request headers
        self.__payment_preference_schema = PaymentPreferenceSchema()  # Schema for single payment preference
        self.__payment_preference_list_schema = PaymentPreferenceSchema(many=True)  # Schema for multiple payment preferences
        self.__create_payment_preference_schema = CreatePaymentPreferenceSchema()  # Schema for creating payment preferences
        self.__update_payment_preference_schema = UpdatePaymentPreferenceSchema()  # Schema for updating payment preferences
        self.__payment_preference_voter = PaymentPreferenceVoter()  # Voter for permission checks
        self.__db = db  # Database session object

    def __del__(self):
        """
        Destructor to ensure the database session is closed when the service is destroyed.
        """
        self.__db.close()

    def _active_preference(self, user_id):
        """
        Retrieves the active payment preference for a given user.

        Args:
            user_id (int): The ID of the user whose active payment preference is to be retrieved.

        Returns:
            dict: The active payment preference data.

        Raises:
            ValueError: If no active payment preference is found for the user.
        """
        # Fetch the active payment preference for the user
        active_preference = payment_preference_crud.get_active_preference(self.__db, user_id)
        if not active_preference:
            raise ValueError("No active payment preference found for the user.")
        return self.__payment_preference_schema.dump(active_preference)

    def CreatePreference(self, request, context):
        """
        Creates a new payment preference for a user.

        Args:
            request: The gRPC request object containing payment preference details.
            context: The gRPC context object.

        Returns:
            A response object containing the created payment preference data.

        Raises:
            PermissionError: If the user does not have permission to create a payment preference.
        """
        try:
            # Validate the request data
            preference_data = self.__create_payment_preference_schema.load(
                MessageToDict(request), unknown=EXCLUDE
            )

            # Check if the user has permission to create a payment preference
            if not self.__payment_preference_voter.can_create(self.__db, preference_data):
                raise PermissionError("Access denied!")

            # Create the payment preference
            new_preference = payment_preference_crud.create(self.__db, preference_data)
            return self.__payment_preference_schema.dump(new_preference)
        except Exception as e:
            self.__del__()
            raise e

    def __createPaymentPreference(self, user_id, preference_data):
        """
        Helper method to create a payment preference for a user.

        Args:
            user_id (int): The ID of the user.
            preference_data (dict): The payment preference data.

        Returns:
            dict: The created payment preference data.
        """
        # Add the user ID to the preference data
        preference_data["user_id"] = user_id

        # Create the payment preference in the database
        new_preference = payment_preference_crud.create(self.__db, preference_data)
        return self.__payment_preference_schema.dump(new_preference)

    def ChangePreferenceType(self, request, context):
        """
        Changes the type of a payment preference.

        Args:
            request: The gRPC request object containing the preference ID and new type.
            context: The gRPC context object.

        Returns:
            A response object containing the updated payment preference data.

        Raises:
            PermissionError: If the user does not have permission to change the preference type.
        """
        try:
            # Fetch the payment preference to be updated
            preference = payment_preference_crud.get(self.__db, request.preference_id)

            # Check if the user has permission to change the preference type
            if not self.__payment_preference_voter.can_update(self.__db, preference):
                raise PermissionError("Access denied!")

            # Update the preference type
            preference.type = request.new_type
            self.__db.commit()
            return self.__payment_preference_schema.dump(preference)
        except Exception as e:
            self.__del__()
            raise e

    def EditPreferenceStatus(self, request, context):
        """
        Edits the status of a payment preference.

        Args:
            request: The gRPC request object containing the preference ID and new status.
            context: The gRPC context object.

        Returns:
            A response object containing the updated payment preference data.

        Raises:
            PermissionError: If the user does not have permission to edit the preference status.
        """
        try:
            # Fetch the payment preference to be updated
            preference = payment_preference_crud.get(self.__db, request.preference_id)

            # Check if the user has permission to edit the preference status
            if not self.__payment_preference_voter.can_update(self.__db, preference):
                raise PermissionError("Access denied!")

            # Update the preference status
            preference.status = request.new_status
            self.__db.commit()
            return self.__payment_preference_schema.dump(preference)
        except Exception as e:
            self.__del__()
            raise e

    def ReadPreferenceByUserId(self, request, context):
        """
        Retrieves all payment preferences for a given user.

        Args:
            request: The gRPC request object containing the user ID.
            context: The gRPC context object.

        Returns:
            A response object containing the list of payment preferences for the user.

        Raises:
            PermissionError: If the user does not have permission to view the preferences.
        """
        try:
            # Fetch the user from the database
            user = user_crud.get_user(self.__db, request.user_id)

            # Check if the user has permission to view the preferences
            if not self.__payment_preference_voter.can_view(self.__db, user):
                raise PermissionError("Access denied!")

            # Fetch and serialize the payment preferences for the user
            preferences = payment_preference_crud.get_by_user_id(self.__db, request.user_id)
            return self.__payment_preference_list_schema.dump(preferences)
        except Exception as e:
            self.__del__()
            raise e
