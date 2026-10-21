# This module defines the UserPaymentMethodApprovalService class, which handles gRPC service
# operations related to user payment method approvals, including creating, updating, and managing
# payment method approval workflows for users.

from google.protobuf.json_format import MessageToDict  # Convert protobuf messages to dictionaries
from datetime import datetime
from marshmallow import EXCLUDE  # Used for schema validation
import proto.communication_proto.payment.payment_pb2  # Communication service protobuf definitions
import proto.communication_proto.payment.payment_pb2_grpc  # Communication service gRPC definitions
import proto.payments_proto.user_payment_method_approvals.user_payment_method_approvals_pb2  # Payment approval protobuf definitions
import proto.payments_proto.user_payment_method_approvals.user_payment_method_approvals_pb2_grpc  # Payment approval gRPC definitions
from voter.user_payment_method_approvals import UserPaymentApprovalVoter  # Voter for permission checks
from enumerations.user_payment_method_approvals import PaymentType, StatusType  # Enums for payment types and statuses
from helper.camel_to_snake import CamelToSnake  # Utility for camelCase to snake_case conversion
from helper.interceptor import RequestHeaderValidatorInterceptor  # Interceptor for validating request headers
from helper.mailer import Mailer  # Email service for notifications
from helper.connection import ConnectionChannel  # gRPC connection management
from sql.crud import (
    user_payment_method_approvals as user_payment_method_approval_crud,  # CRUD operations for payment approvals
    user as user_crud  # CRUD operations for users
)
from sql.schemas.user_payment_method_approvals import (
    CreateUserPaymentMethodApprovalModelSchema,  # Schema for creating payment approvals
    EditUserPaymentMethodApprovaStatuslSchema,  # Schema for editing approval status
    UserPaymentMethodApprovalSchema,  # Schema for payment approval data
)


mailer = Mailer()  # Global mailer instance for sending notifications


class UserPaymentMethodApprovalService(
    proto.payments_proto.user_payment_method_approvals.user_payment_method_approvals_pb2_grpc.UserPaymentMethodApprovalsServiceServicer
):
    """
    gRPC service for managing user payment method approvals.
    
    This service provides methods for creating, updating, and retrieving payment method approvals
    for users, including approval workflows and status management.
    """
    
    def __init__(self, db):
        """
        Initializes the UserPaymentMethodApprovalService with the required dependencies.
        
        Args:
            db: The database session object for performing database operations.
        """
        self.__user_payment_method_approval_schema = UserPaymentMethodApprovalSchema()  # Schema for single approval
        self.__create_user_payment_method_approval_schema = (
            CreateUserPaymentMethodApprovalModelSchema()  # Schema for creating approvals
        )
        self.__edit_user_payment_method_approval_schema = (
            EditUserPaymentMethodApprovaStatuslSchema()  # Schema for editing approval status
        )
        self.__camel_to_snake = CamelToSnake()  # Utility for case conversion
        self.__interceptor = RequestHeaderValidatorInterceptor()  # Request validation interceptor
        self.__user_payment_approval_voter = UserPaymentApprovalVoter()  # Voter for permission checks
        self.__read_approvals_details_list_schema = UserPaymentMethodApprovalSchema(
            many=True  # Schema for multiple approvals
        )
        self.__read_approvals_details_schema = UserPaymentMethodApprovalSchema()  # Schema for single approval
        self.__db = db  # Database session

    def __del__(self):
        """
        Destructor to ensure the database session is closed when the service is destroyed.
        """
        self.__db.close()

    def _is_approved(self, user_id, method):
        """
        Checks if a user has an approved payment method of the specified type.
        
        Args:
            user_id (int): The ID of the user to check.
            method (str): The payment method type to check for approval.
            
        Returns:
            The approved payment method if found.
            
        Raises:
            PermissionError: If the user doesn't have an approved payment method of the specified type.
        """
        is_approved = user_payment_method_approval_crud._is_approved_user(
            self.__db, user_id, method
        )
        if is_approved and is_approved is not None:
            return is_approved
        else:
            raise PermissionError(
                f"This User {method.upper()} Payment Method not approved!"
            )

    # Create call
    def CreateUserPaymentMethodApproval(self, request, context):
        try:
            request_data = self.__camel_to_snake._decode_keys(
                MessageToDict(request.details)
            )

            logged_in_user = self.__interceptor._get_logged_in_user()
            if "user_id" not in request_data:
                request_data["user_id"] = logged_in_user.id

            check_approval = (
                user_payment_method_approval_crud._check_approval_by_user(
                    self.__db, request_data["user_id"], request_data["payment_method_type"]
                )
            )
            if not self.__user_payment_approval_voter._default(
                self.__db, "add", check_approval
            ):
                raise PermissionError("Access denied!")

            if check_approval:
                raise PermissionError("Your request has been already stored.")

            user = user_crud.get_user(self.__db, request_data["user_id"])
            if not user:
                raise PermissionError("Please provide valid user!")

            request_data["created_by"] = logged_in_user.id
            request_data["status"] = "approved"
            request_data["user_id"] = user.id
            request_data["approved_at"] = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            # print("Email send to user")
            # subject = "Payment Method Approved"
            # to = username
            # body = (
            #     "Hello {username}, Your requested payment method is approved."
            # )
            # from_add = "Paymentgatway <request@mg.example.com>"

            check = user_payment_method_approval_crud._get_approvals_by_user(self.__db, request_data["user_id"])
            if len(check) == 0:
                request_data["is_default"] = True

            request_data["status"] = "approved"
            result = self.__create_user_payment_method_approval_schema.load(
                request_data, session=self.__db, unknown=EXCLUDE
            )

            approval = user_payment_method_approval_crud._create(self.__db, result)
            # if approval:
            # mailer._send_mail(subject, to, body, from_add)
            self.__db.close()

            return proto.payments_proto.user_payment_method_approvals.user_payment_method_approvals_pb2.CreateUserPaymentMethodApprovalResponse(
                message="User payment method approval created successfully."
            )
        except Exception as e:
            self.__del__()
            raise PermissionError(str(e))
        
    def SendPaymentSetupDetails(self, request, context):
        try:
            channel = ConnectionChannel.grpc_communication_channel()
            client = (
                proto.communication_proto.payment.payment_pb2_grpc.SendPaymentServiceStub(
                    channel
                )
            )

            data = request.details
            logged_in_user = self.__interceptor._get_logged_in_user()
            request_data = {
                "name": logged_in_user.name,
                "username": logged_in_user.username,
                "to": "support@example.com",
            }

            response = client.SendPaymentSetupEmail(
                proto.communication_proto.payment.payment_pb2.SendPaymentSetupDetailsRequest(
                    send_payment_setup_details=request_data
                )
            )
            
            return proto.payments_proto.user_payment_method_approvals.user_payment_method_approvals_pb2.SendPaymentSetupDetailsResponse(
                result= response.result
            )
        except Exception as e:
            self.__del__()
            raise PermissionError(str(e))
            

    def EditUserStatus(self, request, context):
        try:
            approval = user_payment_method_approval_crud._get_by_id(
                self.__db, request.id
            )
            if not approval:
                raise PermissionError("User payment method approval record not found.")

            if not self.__user_payment_approval_voter._default(
                self.__db, "edit", approval
            ):
                raise PermissionError("Access denied!")

            data = self.__camel_to_snake._decode_keys(MessageToDict(request))
            result = self.__edit_user_payment_method_approval_schema.load(
                data, session=self.__db, unknown=EXCLUDE
            )
            user_payment_method_approval_detail = (
                user_payment_method_approval_crud._edit_status(
                    self.__db, approval, result
                )
            )

            result = self.__user_payment_method_approval_schema.dump(
                user_payment_method_approval_detail
            )

            # Email Send to user
            self.__db.close()
            return proto.payments_proto.user_payment_method_approvals.user_payment_method_approvals_pb2.EditUserStatusResponse(
                details=result
            )
        except Exception as e:
            self.__del__()
            raise PermissionError(str(e))

    def ReadPaymentApprovalByUserId(self, request, context):
        try:
            logged_in_user = self.__interceptor._get_logged_in_user()
            if not logged_in_user:
                raise PermissionError("Access denied!")

            user_id = None

            is_approval = user_payment_method_approval_crud._get_all_approvals_list(
                self.__db, user_id= user_id , payment_method_type= request.payment_method_type, is_default= request.is_default
            )
            if not is_approval:
                raise PermissionError("User payment method approval record not found.")

           
            result = self.__read_approvals_details_schema.dump(is_approval["approvals_list"], many= True)

            self.__db.close()

            return proto.payments_proto.user_payment_method_approvals.user_payment_method_approvals_pb2.ReadPaymentApprovalByUserIdResponse(
                details=result
            )
        except Exception as e:
            self.__del__()
            raise PermissionError(str(e))

    def ListPaymentApprovals(self, request, context):
        try:
            compauser_idny_id = request.user_id
            status = request.status
            logged_in_user = self.__interceptor._get_logged_in_user()
            if logged_in_user:
                user_id = logged_in_user.id
                status = StatusType.APPROVED
            else:
                pass

            approvals_details = (
                user_payment_method_approval_crud._get_all_approvals_list(
                    self.__db,
                    filter=request.filter,
                    order_by=request.order_by,
                    order_direction=request.order_direction,
                    limit=request.limit,
                    page=request.page,
                    user_id=user_id,
                    payment_method_type=request.payment_method_type,
                    status=status,
                    is_default=request.is_default,
                )
            )

            if not approvals_details:
                raise PermissionError("No user payment method approval records found.")

            meta = {
                "page": approvals_details["page"],
                "limit": approvals_details["limit"],
                "current_items": approvals_details["item"],
                "total_items": approvals_details["total_items"],
            }

            approvals_details = self.__read_approvals_details_list_schema.dump(
                approvals_details["approvals_list"]
            )

            self.__db.close()

            return proto.payments_proto.user_payment_method_approvals.user_payment_method_approvals_pb2.ListPaymentApprovalsResponse(
                meta=meta, approvals=approvals_details
            )
        except Exception as e:
            self.__del__()
            raise PermissionError(str(e))