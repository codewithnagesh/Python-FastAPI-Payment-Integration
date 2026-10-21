import typing as t

import grpc
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import JSONResponse
from google.protobuf.json_format import MessageToDict
from starlette.status import HTTP_204_NO_CONTENT

import proto.payments_proto.user_payment_methods.user_payment_methods_pb2
import proto.payments_proto.user_payment_methods.user_payment_methods_pb2_grpc
from helper.auth.auth_handler import JWTBearer
from helper.camel_to_snake import CamelToSnake
from helper.connection import ConnectionChannel
from helper.error_handling import ErrorHanding
from models.user_payment_methods import (
    CreateUserPaymentMethod,
    UpdateUserPaymentMethod,
    StoreAuthAccess,
    Type,
    Preference,
    OrderDirection,
    StatusType,
    DefaultDetailsRequest,
)

router = APIRouter(
    prefix="/user-payment-method",
    tags=["User Payment Methods"],
    responses={404: {"description": "Endpoint Not found"}},
)
camel_to_snake = CamelToSnake()


# Create user payment method
@router.post("")
def create_payment_method(
    data: CreateUserPaymentMethod,
    channel: t.Any = Depends(ConnectionChannel.grpc_payments_channel),
    d: t.Any = Depends(JWTBearer()),
) -> JSONResponse:
    client = proto.payments_proto.user_payment_methods.user_payment_methods_pb2_grpc.UserPaymentMethodsServiceStub(
        channel
    )
    formated_data = camel_to_snake._decode_keys(data.dict())
    try:
        grpc_request = proto.payments_proto.user_payment_methods.user_payment_methods_pb2.CreateUserPaymentMethodRequest(
            user_payment_method_data=formated_data
        )

        response = client.CreateUserPaymentMethod(grpc_request)
    except grpc.RpcError as e:
        raise HTTPException(
            status_code=400, detail=ErrorHanding._remove_data(e.details())
        )

    result = MessageToDict(response, including_default_value_fields=True)
    if result:
        return camel_to_snake._decode_keys(result)
    else:
        return {"message": "Failed to create!"}, 404


# Get active payment method
@router.get("/active")
def get_active_payment_method(
    user_id: int,
    payment_method_type: t.Literal[
        Type.paysafe, Type.authnet, Type.jupiter, Type.paypal, Type.applepay, Type.googlepay
    ] = None,
    is_default: bool = False,
    channel: t.Any = Depends(ConnectionChannel.grpc_payments_channel),
) -> JSONResponse:
    client = proto.payments_proto.user_payment_methods.user_payment_methods_pb2_grpc.UserPaymentMethodsServiceStub(
        channel
    )
    try:
        result = client.ReadUserActivePaymentMethod(
            proto.payments_proto.user_payment_methods.user_payment_methods_pb2.ReadUserActivePaymentMethodRequest(
                user_id=user_id,
                payment_method_type=payment_method_type,
                is_default=is_default,
                
            )
        )
    except grpc.RpcError as e:
        raise HTTPException(
            status_code=400, detail=ErrorHanding._remove_data(e.details())
        )

    response = camel_to_snake._decode_keys(MessageToDict(result, including_default_value_fields=True))
    return response['response']


# Find user current active payment method
@router.get("")
def get_current_payment_method(
    preference: t.Literal[Preference.user],
    id: int,
    user_id: t.Optional[int] = None,
    payment_method_type: t.Literal[
        Type.paysafe, Type.authnet, Type.jupiter
    ] = Type.paysafe,
    channel: t.Any = Depends(ConnectionChannel.grpc_payments_channel),
    d: t.Any = Depends(JWTBearer()),
) -> JSONResponse:
    client = proto.payments_proto.user_payment_methods.user_payment_methods_pb2_grpc.UserPaymentMethodsServiceStub(
        channel
    )
    try:
        result = client.ReadUserCurrentPaymentMethod(
            proto.payments_proto.user_payment_methods.user_payment_methods_pb2.ReadUserCurrentPaymentMethodRequest(
                preference=preference,
                id=id,
                user_id=user_id,
                payment_method_type=payment_method_type,
            )
        )
    except grpc.RpcError as e:
        raise HTTPException(
            status_code=400, detail=ErrorHanding._remove_data(e.details())
        )

    response = MessageToDict(result, including_default_value_fields=True)
    return camel_to_snake._decode_keys(response)


# Update user payment method
@router.put("/{id:int}")
def update_payment_method(
    id: int,
    request_data: UpdateUserPaymentMethod,
    channel: t.Any = Depends(ConnectionChannel.grpc_payments_channel),
    d: t.Any = Depends(JWTBearer()),
) -> JSONResponse:
    client = proto.payments_proto.user_payment_methods.user_payment_methods_pb2_grpc.UserPaymentMethodsServiceStub(
        channel
    )
    formated_data = camel_to_snake._decode_keys(request_data.dict())
    try:
        grpc_request = proto.payments_proto.user_payment_methods.user_payment_methods_pb2.UpdateUserPaymentMethodRequest(
            id=id, user_payment_method_data=formated_data
        )
        result = client.UpdateUserPaymentMethod(grpc_request)

    except grpc.RpcError as e:
        raise HTTPException(
            status_code=400, detail=ErrorHanding._remove_data(e.details())
        )

    response = MessageToDict(
        result.user_payment_method_data, including_default_value_fields=True
    )
    if response:
        return camel_to_snake._decode_keys(response)
    else:
        raise HTTPException(status_code=404, detail="Failed to update record")


# Soft Delete user payment method for history mentained
@router.delete("/{id:int}")
def delete_payment_method(
    id: int,
    channel: t.Any = Depends(ConnectionChannel.grpc_payments_channel),
    d: t.Any = Depends(JWTBearer()),
) -> JSONResponse:
    client = proto.payments_proto.user_payment_methods.user_payment_methods_pb2_grpc.UserPaymentMethodsServiceStub(
        channel
    )
    try:
        response = client.SoftDeleteUserPaymentMethod(
            proto.payments_proto.user_payment_methods.user_payment_methods_pb2.SoftDeleteUserPaymentMethodRequest(
                id=id
            )
        )

    except grpc.RpcError as e:
        raise HTTPException(
            status_code=400, detail=ErrorHanding._remove_data(e.details())
        )

    if response:
        return Response(status_code=HTTP_204_NO_CONTENT)
    else:
        return {"message": "Failed to delete!"}, 404


# Store the Authorizenet auth access
@router.post("/authorizenet/store-auth-access")
def store_authorizenet_auth_access(
    request: StoreAuthAccess,
    channel: t.Any = Depends(ConnectionChannel.grpc_payments_channel),
    d: t.Any = Depends(JWTBearer()),
) -> JSONResponse:
    client = proto.payments_proto.user_payment_methods.user_payment_methods_pb2_grpc.UserPaymentMethodsServiceStub(
        channel
    )
    try:
        response = client.StoreAuthorizenetAuthAccess(
            proto.payments_proto.user_payment_methods.user_payment_methods_pb2.StoreAuthorizenetAuthAccessRequest(
                auth_login_id=request.auth_login_id,
                auth_transaction_key=request.auth_transaction_key,
                auth_client_key=request.auth_client_key,
                user_id=request.user_id,
                payment_method_type=request.payment_method_type,
            )
        )

    except grpc.RpcError as e:
        raise HTTPException(
            status_code=400, detail=ErrorHanding._remove_data(e.details())
        )

    result = MessageToDict(response, including_default_value_fields=True)
    return camel_to_snake._decode_keys(result)

# update Authorizenet auth access details
@router.put("/authorizenet/update-auth-access")
def update_authorizenet_auth_access(
    request: StoreAuthAccess,
    channel: t.Any = Depends(ConnectionChannel.grpc_payments_channel),
    d: t.Any = Depends(JWTBearer()),
) -> JSONResponse:
    client = proto.payments_proto.user_payment_methods.user_payment_methods_pb2_grpc.UserPaymentMethodsServiceStub(
        channel
    )
    try:
        response = client.UpdateAuthorizenetAuthAccess(
            proto.payments_proto.user_payment_methods.user_payment_methods_pb2.UpdateAuthorizenetAuthAccessRequest(
                auth_login_id=request.auth_login_id,
                auth_transaction_key=request.auth_transaction_key,
                auth_client_key=request.auth_client_key,
                user_id=request.user_id,
                payment_method_type=request.payment_method_type,
            )
        )

    except grpc.RpcError as e:
        raise HTTPException(
            status_code=400, detail=ErrorHanding._remove_data(e.details())
        )

    result = MessageToDict(response, including_default_value_fields=True)
    return camel_to_snake._decode_keys(result)

# List user payment methods
@router.get("/list-user-payment-methods")
def list_user_payment_methods(
    filter: t.Optional[str] = "",
    order_by: t.Optional[str] = "id",
    order_direction: t.Literal[OrderDirection.desc, OrderDirection.asc] = None,
    payment_method_type: t.Literal[Type.paysafe, Type.authnet, Type.jupiter, Type.paypal, Type.applepay, Type.googlepay] = None,
    status: t.Literal[
        StatusType.approved,
        StatusType.declined,
        StatusType.desabled,
        StatusType.pending,
    ] = None,
    payment_preference_id: t.Optional[int] = None,
    user_id: t.Optional[int] = None,
    page: t.Optional[int] = 1,
    limit: t.Optional[int] = 10,
    start_date: t.Optional[str] = None,
    end_date: t.Optional[str] = None,
    channel: t.Any = Depends(ConnectionChannel.grpc_payments_channel),
    d: t.Any = Depends(JWTBearer()),
) -> JSONResponse:
    client = proto.payments_proto.user_payment_methods.user_payment_methods_pb2_grpc.UserPaymentMethodsServiceStub(
        channel
    )
    try:
        grpc_request = proto.payments_proto.user_payment_methods.user_payment_methods_pb2.ListUserPaymentMethodsRequest(
            filter=filter,
            order_by=order_by,
            status=status,
            order_direction=order_direction,
            payment_method_type=payment_method_type,
            user_id=user_id,
            payment_preference_id=payment_preference_id,
            page=page,
            limit=limit,
            start_date=start_date,
            end_date=end_date,
        )
        response = client.ListUserPaymentMethods(grpc_request)
    except grpc.RpcError as e:
        raise HTTPException(
            status_code=400, detail=ErrorHanding._remove_data(e.details())
        )

    result = MessageToDict(response, including_default_value_fields=True)
    return camel_to_snake._decode_keys(result)

# Set user default payemt
@router.patch("/set-default")
def set_default_payment_method(
    request: DefaultDetailsRequest,
    channel: t.Any = Depends(ConnectionChannel.grpc_payments_channel),
    d: t.Any = Depends(JWTBearer()),
) -> JSONResponse:
    try:
        client = proto.payments_proto.user_payment_methods.user_payment_methods_pb2_grpc.UserPaymentMethodsServiceStub(
            channel
        )
        grpc_request = proto.payments_proto.user_payment_methods.user_payment_methods_pb2.SetDefaultPaymentMethodRequest(
            payment_method=request.payment_method,
            user_id=request.user_id
        )
        response = client.SetDefaultPaymentMethod(grpc_request)
    except grpc.RpcError as e:
        raise HTTPException(
            status_code=400, detail=ErrorHanding._remove_data(e.details())
        )

    result = MessageToDict(response, including_default_value_fields=True)
    if result:
        return camel_to_snake._decode_keys(result)
    else:
        return {"message": "Failed to set Default payment method!"}, 404