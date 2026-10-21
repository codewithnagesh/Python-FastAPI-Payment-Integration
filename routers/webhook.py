import typing as t
import grpc
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from typing import Any
from google.protobuf.json_format import MessageToDict
from helper.auth.auth_handler import JWTBearer
from helper.camel_to_snake import CamelToSnake
from helper.connection import ConnectionChannel
from helper.error_handling import ErrorHanding
import proto.payments_proto.paysafe_webhook.paysafe_webhook_pb2
import proto.payments_proto.paysafe_webhook.paysafe_webhook_pb2_grpc


router = APIRouter(
    prefix="/webhook",
    tags=["Webhooks"],
    responses={404: {"description": "Endpoint Not found"}},
    dependencies=[Depends(JWTBearer())],
)
camel_to_snake = CamelToSnake()


# Root Post check call
@router.post("")
async def webhook_details_handler(
    request: Request,
    channel: t.Any = Depends(ConnectionChannel.grpc_payments_channel),
) -> JSONResponse:
    client = proto.payments_proto.paysafe_webhook.paysafe_webhook_pb2_grpc.WebhookServiceStub(
        channel
    )
    try:
        data = await request.json()
        print(data)
        response = client.CreateWebhook(
            proto.payments_proto.paysafe_webhook.paysafe_webhook_pb2.WebhookDetailsRequest(
                message=str(data)
            )
        )
    except grpc.RpcError as e:
        raise HTTPException(
            status_code=400, detail=ErrorHanding._remove_data(e.details())
        )
    result = response.message
    if result:
        return result
    else:
        return {"message": "Failed to received data !"}, 404


# Find Merchant Details
@router.get("/merchant-details")
async def merchant_details_handler(
    request: Request,
    channel: t.Any = Depends(ConnectionChannel.grpc_payments_channel),
) -> JSONResponse:
    client = proto.payments_proto.paysafe_webhook.paysafe_webhook_pb2_grpc.WebhookServiceStub(
        channel
    )
    try:
        response = client.GetMerchantDetails(
            proto.payments_proto.paysafe_webhook.paysafe_webhook_pb2.MerchantDetailsRequest()
        )

    except grpc.RpcError as e:
        print("grpc.RpcError")
        raise HTTPException(
            status_code=400, detail=ErrorHanding._remove_data(e.details())
        )
    result = MessageToDict(response, including_default_value_fields=True)
    if result:
        print(f"Merchant Details: {result}")
        return {"message": "Merchant details request received"}
    else:
        return {"message": "Failed to received merchant details request !"}, 404


# Notifications
@router.get("/notifications")
async def notifications_handler(
    request: Request,
    channel: t.Any = Depends(ConnectionChannel.grpc_payments_channel),
) -> JSONResponse:
    body = await request.json()
    client = proto.payments_proto.paysafe_webhook.paysafe_webhook_pb2_grpc.WebhookServiceStub(
        channel
    )
    try:
        response = client.GetNotifications(
            proto.payments_proto.paysafe_webhook.paysafe_webhook_pb2.NotificationsRequest()
        )
    except grpc.RpcError as e:
        raise HTTPException(
            status_code=400, detail=ErrorHanding._remove_data(e.details())
        )

    result = MessageToDict(response.message, including_default_value_fields=True)
    if result:
        print(f"Notifications: {result}")
        return camel_to_snake._decode_keys(result)
    else:
        return {"message": "Failed to Failed to received notification request !!"}, 404


# Transaction Update
@router.get("/transaction-update")
async def transaction_update_handler(
    request: Request,
    channel: t.Any = Depends(ConnectionChannel.grpc_payments_channel),
) -> JSONResponse:
    data = await request.json()
    client = proto.payments_proto.paysafe_webhook.paysafe_webhook_pb2_grpc.WebhookServiceStub(
        channel
    )
    try:
        response = client.ProcessTransactionUpdate(
            proto.payments_proto.paysafe_webhook.paysafe_webhook_pb2.TransactionUpdateRequest()
        )
    except grpc.RpcError as e:
        raise HTTPException(
            status_code=400, detail=ErrorHanding._remove_data(e.details())
        )
    result = MessageToDict(response, including_default_value_fields=True)
    if result:
        print(response)
        return camel_to_snake._decode_keys(result)
    else:
        return {"message": "Failed to received transaction update webhook !"}, 404


# Customer Details
@router.get("/customer-details")
async def customer_details_handler(
    request: Request,
    channel: t.Any = Depends(ConnectionChannel.grpc_payments_channel),
) -> JSONResponse:
    data = await request.json()
    client = proto.payments_proto.paysafe_webhook.paysafe_webhook_pb2_grpc.WebhookServiceStub(
        channel
    )
    try:
        response = client.ProcessCustomerDetails(
            proto.payments_proto.paysafe_webhook.paysafe_webhook_pb2.CustomerDetailsRequest(
                **data
            )
        )
    except grpc.RpcError as e:
        raise HTTPException(
            status_code=400, detail=ErrorHanding._remove_data(e.details())
        )
    result = MessageToDict(response, including_default_value_fields=True)
    if result:
        print(result)
        return camel_to_snake._decode_keys(result)
    else:
        return {"message": "Failed to received customer details webhook !"}, 404
