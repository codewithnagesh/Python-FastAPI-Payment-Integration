import typing as t

import grpc
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from google.protobuf.json_format import MessageToDict

import proto.payments_proto.user_payment_method_approvals.user_payment_method_approvals_pb2
import proto.payments_proto.user_payment_method_approvals.user_payment_method_approvals_pb2_grpc
from helper.auth.auth_handler import JWTBearer
from helper.camel_to_snake import CamelToSnake
from helper.connection import ConnectionChannel
from helper.error_handling import ErrorHanding
from models.user_payment_method_approvals import (
    CreatePaymentApproval,
    SendPaymentSetupDetails,
    EditUserStatus,
)
from models.user_payment_method_approvals import StatusType, PaymentType

router = APIRouter(
    prefix="/payment-approval",
    tags=["User Payment Method Approval"],
    responses={404: {"description": "Endpoint Not found"}},
    dependencies=[Depends(JWTBearer())],
)
camel_to_snake = CamelToSnake()


# For create user Payment methed approval request 
@router.post("")
def create_user_payment_method_approval(
    data: CreatePaymentApproval,
    channel: t.Any = Depends(ConnectionChannel.grpc_payments_channel),
    d: t.Any = Depends(JWTBearer()),
) -> JSONResponse:
    client = proto.payments_proto.user_payment_method_approvals.user_payment_method_approvals_pb2_grpc.UserPaymentMethodApprovalsServiceStub(
        channel
    )
    formated_data = camel_to_snake._decode_keys(data.dict())

    try:
        grpc_request = proto.payments_proto.user_payment_method_approvals.user_payment_method_approvals_pb2.CreateUserPaymentMethodApprovalRequest(
            details=formated_data
        )

        user_payment_method_approval_data = client.CreateUserPaymentMethodApproval(
            grpc_request
        )

    except grpc.RpcError as e:
        raise HTTPException(
            status_code=400, detail=ErrorHanding._remove_data(e.details())
        )
    result = MessageToDict(
        user_payment_method_approval_data, including_default_value_fields=True
    )
    if result:
        return camel_to_snake._decode_keys(result)
    else:
        return {"message": "Failed to create!"}, 404

# Send Payment setup Details to user
@router.post("/send-setup-details")
def send_payment_setup_form_details(
    data: SendPaymentSetupDetails,
    channel: t.Any = Depends(ConnectionChannel.grpc_payments_channel),
    d: t.Any = Depends(JWTBearer()),
) -> JSONResponse:
    client = proto.payments_proto.user_payment_method_approvals.user_payment_method_approvals_pb2_grpc.UserPaymentMethodApprovalsServiceStub(
        channel
    )
    formated_data = camel_to_snake._decode_keys(data.dict())

    try:
        grpc_request = proto.payments_proto.user_payment_method_approvals.user_payment_method_approvals_pb2.SendPaymentSetupDetailsRequest(
            details=formated_data
        )

        response = client.SendPaymentSetupDetails(
            grpc_request
        )

    except grpc.RpcError as e:
        raise HTTPException(
            status_code=400, detail=ErrorHanding._remove_data(e.details())
        )
    print(response.result)
    if response.result:
        return response.result
    else:
        raise HTTPException(status_code=404, detail="Failed to send payment detail!")

# Get user payement method approval status
@router.get("")
def payment_approvals_by_user_id(
    user_id: int = None,
    payment_method_type: t.Literal[
        PaymentType.paysafe, PaymentType.authnet, PaymentType.jupiter, PaymentType.paypal, PaymentType.stripe, PaymentType.googlepay, PaymentType.googlepay
    ] = None,
    is_default: t.Literal["true", "false"] = None,
    channel: t.Any = Depends(ConnectionChannel.grpc_payments_channel),
) -> JSONResponse:
    client = proto.payments_proto.user_payment_method_approvals.user_payment_method_approvals_pb2_grpc.UserPaymentMethodApprovalsServiceStub(
        channel
    )
    try:
        grpc_request = proto.payments_proto.user_payment_method_approvals.user_payment_method_approvals_pb2.ReadPaymentApprovalByUserIdRequest(
            user_id=user_id,
            payment_method_type=payment_method_type,
            is_default=is_default,
        )
        response = client.ReadPaymentApprovalByUserId(grpc_request)
    except grpc.RpcError as e:
        raise HTTPException(
            status_code=400, detail=ErrorHanding._remove_data(e.details())
        )

    result = MessageToDict(response, including_default_value_fields=True)

    if result:
        return camel_to_snake._decode_keys(result)["details"]
    else:
        return {"message": "Failed to read data!"}, 404

# Edit user payment method approval status
@router.put("/{id:int}")
def edit_user_payment_method_approval_status(
    id: int,
    status: EditUserStatus,
    channel: t.Any = Depends(ConnectionChannel.grpc_payments_channel),
) -> JSONResponse:
    client = proto.payments_proto.user_payment_method_approvals.user_payment_method_approvals_pb2_grpc.UserPaymentMethodApprovalsServiceStub(
        channel
    )
    try:
        response = client.EditUserStatus(
            proto.payments_proto.user_payment_method_approvals.user_payment_method_approvals_pb2.EditUserStatusRequest(
                id=id, status=status.status
            )
        )
    except grpc.RpcError as e:
        raise HTTPException(
            status_code=400, detail=ErrorHanding._remove_data(e.details())
        )
    result = MessageToDict(response.details, including_default_value_fields=True)
    if result:
        return camel_to_snake._decode_keys(result)
    else:
        return {"message": "Failed to edit!"}, 404