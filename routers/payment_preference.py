# This module defines FastAPI routes for payment preference operations in the payment API service.
# These routes handle user payment preferences, including creating, updating, and managing
# payment method preferences through gRPC services.

import typing as t  # Type hints for better code documentation
import grpc  # gRPC communication
from fastapi import APIRouter, Depends, HTTPException  # FastAPI framework components
from fastapi.responses import JSONResponse  # JSON response handling
from google.protobuf.json_format import MessageToDict  # Convert protobuf messages to dictionaries
from helper.error_handling import ErrorHanding  # Error handling utilities
import proto.payments_proto.payment_preference.payment_preference_pb2  # Payment preference protobuf definitions
import proto.payments_proto.payment_preference.payment_preference_pb2_grpc  # Payment preference gRPC definitions
from helper.auth.auth_handler import JWTBearer  # JWT authentication handler
from helper.camel_to_snake import CamelToSnake  # Utility for case conversion
from models.payment_preference import (
    AddPreference,  # Model for adding payment preferences
    ChangePreferenceType,  # Model for changing preference types
    Type,  # Enum for payment method types
)
from helper.connection import ConnectionChannel  # gRPC connection management

camel_to_snake = CamelToSnake()  # Global instance for case conversion


router = APIRouter(
    prefix="/user-payment-preference",  # Base path for all payment preference endpoints
    tags=["Payment Preference"],  # OpenAPI tag for documentation
    responses={404: {"description": "Endpoint Not found"}},  # Default error response
    dependencies=[Depends(JWTBearer())],  # JWT authentication required for all endpoints
)

# Set a user payment preference
@router.post("")
def create_preference(
    preference: AddPreference,
    channel: t.Any = Depends(ConnectionChannel.grpc_payments_channel),
) -> JSONResponse:
    request = camel_to_snake._decode_keys(preference.dict())
    client = proto.payments_proto.payment_preference.payment_preference_pb2_grpc.PaymentPreferenceServiceStub(
        channel
    )

    try:
        response = client.CreatePreference(
            proto.payments_proto.payment_preference.payment_preference_pb2.CreatePreferenceRequest(
                preference_details=request
            )
        )

    except grpc.RpcError as e:
        raise HTTPException(
            status_code=400, detail=ErrorHanding._remove_data(e.details())
        )

    result = MessageToDict(response)
    if result:
        return camel_to_snake._decode_keys(result)
    else:
        return {"Failed to create payment preference !"}, 404

# Find user active payment preference
@router.get("")
def get_active_preference_by_user_id(
    user_id: int = None,
    payment_method_type: t.Literal[Type.paypal, Type.paysafe, Type.googlepay, Type.applepay, Type.authnet, Type.jupiter] = Type.authnet,
    channel: t.Any = Depends(ConnectionChannel.grpc_payments_channel),
) -> JSONResponse:
    client = proto.payments_proto.payment_preference.payment_preference_pb2_grpc.PaymentPreferenceServiceStub(
        channel
    )
    try:
        grpc_request = proto.payments_proto.payment_preference.payment_preference_pb2.ReadPreferenceByUserIdRequest(
            user_id=user_id,
            payment_method_type=payment_method_type,
        )
        response = client.ReadPreferenceByUserId(grpc_request)
    except grpc.RpcError as e:
        raise HTTPException(
            status_code=400, detail=ErrorHanding._remove_data(e.details())
        )
    result = MessageToDict(response)
    if result:
        return camel_to_snake._decode_keys(result)["response"]
    else:
        return {"Failed to get payment preference !"}, 404

# Set preference as inactive status 
@router.put("/inactive/{id:int}")
def inactive_preference_status(
    id: int,
    channel: t.Any = Depends(ConnectionChannel.grpc_payments_channel),
) -> JSONResponse:
    client = proto.payments_proto.payment_preference.payment_preference_pb2_grpc.PaymentPreferenceServiceStub(
        channel
    )
    try:
        response = client.EditPreferenceStatus(
            proto.payments_proto.payment_preference.payment_preference_pb2.EditPreferenceStatusRequest(
                id=id
            )
        )

    except grpc.RpcError as e:
        raise HTTPException(
            status_code=400, detail=ErrorHanding._remove_data(e.details())
        )
    result = MessageToDict(response.response)
    if result:
        return camel_to_snake._decode_keys(result)
    else:
        return {"Failed to create payment preference !"}, 404

# Update preference type
@router.put("/change-type/{id:int}")
def change_preference_type(
    id: int,
    preference: ChangePreferenceType,
    channel: t.Any = Depends(ConnectionChannel.grpc_payments_channel),
) -> JSONResponse:
    request = camel_to_snake._decode_keys(preference.dict())
    client = proto.payments_proto.payment_preference.payment_preference_pb2_grpc.PaymentPreferenceServiceStub(
        channel
    )
    try:
        response = client.ChangePreferenceType(
            proto.payments_proto.payment_preference.payment_preference_pb2.ChangePreferenceTypeRequest(
                id=id, preference_details=request
            )
        )
    except grpc.RpcError as e:
        raise HTTPException(
            status_code=400, detail=ErrorHanding._remove_data(e.details())
        )
    result = MessageToDict(response.response)
    if result:
        return camel_to_snake._decode_keys(result)
    else:
        return {"Failed to change payment preference type !"}, 404
