# This module defines FastAPI routes for transaction-related operations in the payment API service.
# These routes handle payment processing, refunds, and transaction management through gRPC services.

import typing as t  # Type hints for better code documentation
import grpc, json, ast  # gRPC communication, JSON processing, and AST parsing
from fastapi import APIRouter, Depends, HTTPException  # FastAPI framework components
from fastapi.responses import JSONResponse  # JSON response handling
from google.protobuf.json_format import MessageToDict  # Convert protobuf messages to dictionaries

import proto.payments_proto.transactions.transactions_pb2  # Transaction protobuf definitions
import proto.payments_proto.transactions.transactions_pb2_grpc  # Transaction gRPC definitions
from helper.auth.auth_handler import JWTBearer  # JWT authentication handler
from helper.camel_to_snake import CamelToSnake  # Utility for case conversion
from helper.connection import ConnectionChannel  # gRPC connection management
from helper.error_handling import ErrorHanding  # Error handling utilities
from models.transactions import (
    ProfilePayment,  # Model for profile-based payments
    CreatePayment,  # Model for creating payments
    RefundProcess,  # Model for refund processing
    RefundTransaction,  # Model for refund transactions
)
from models.user_payment_methods import Type, OrderDirection  # Enums for payment types and ordering

camel_to_snake = CamelToSnake()  # Global instance for case conversion


router = APIRouter(
    prefix="/transaction",  # Base path for all transaction endpoints
    tags=["Transactions"],  # OpenAPI tag for documentation
    responses={404: {"description": "Endpoint Not found"}},  # Default error response
)

# Request payment based on payment profile type (Like subscription payment methods)
@router.post("/user-profile-payment/{payment_method}")
def delay_payment_from_customer_payment_profile_baised(
    payment_method: t.Literal[Type.paysafe, Type.paysafe, Type.authnet, Type.jupiter, Type.googlepay, Type.applepay],
    payment_detail: ProfilePayment,
    channel: t.Any = Depends(ConnectionChannel.grpc_payments_channel),
    dependencies=Depends(JWTBearer()),
) -> JSONResponse:
    client = (
        proto.payments_proto.transactions.transactions_pb2_grpc.TransactionServiceStub(
            channel
        )
    )
    try:
        response = client.ProfilePayment(
            proto.payments_proto.transactions.transactions_pb2.ProfilePaymentRequest(
                user_id=payment_detail.user_id,
                invoice_id=payment_detail.invoice_id,
                payment_method=payment_method,
            )
        )

    except grpc.RpcError as e:
        raise HTTPException(
            status_code=400, detail=ErrorHanding._remove_data(e.details())
        )

    result = json.loads(response.response)
    if result:
        return camel_to_snake._decode_keys(result)
    else:
        raise HTTPException(status_code=400, detail="Failed to create Payment!")

# Create instant payment
@router.post("/checkout-payment/{payment_method}")
def instant_payment_from_authnet_paysafe(
    payment_method: t.Literal[Type.paysafe, Type.authnet, Type.jupiter],
    payment_detail: CreatePayment,
    channel: t.Any = Depends(ConnectionChannel.grpc_payments_channel),
) -> JSONResponse:
    client = (
        proto.payments_proto.transactions.transactions_pb2_grpc.TransactionServiceStub(
            channel
        )
    )
    r = payment_detail.dict()
    try:
        response = client.CheckoutPayment(
            proto.payments_proto.transactions.transactions_pb2.CheckoutPaymentRequest(
                payment_detail=r, payment_method=payment_method
            )
        )

    except grpc.RpcError as e:
        raise HTTPException(
            status_code=400, detail=ErrorHanding._remove_data(e.details())
        )

    result = json.loads(response.response)
    if result:
        return result
    else:
        raise HTTPException(status_code=400, detail="Failed to create Payment!")


# Pull transection details by transection id
@router.get("/{id:int}")
def get_transaction_by_id(
    id: int,
    channel: t.Any = Depends(ConnectionChannel.grpc_payments_channel),
    dependencies=Depends(JWTBearer()),
) -> JSONResponse:
    client = (
        proto.payments_proto.transactions.transactions_pb2_grpc.TransactionServiceStub(
            channel
        )
    )
    try:
        response = client.ReadTransaction(
            proto.payments_proto.transactions.transactions_pb2.ReadTransactionRequest(
                id=id
            )
        )
    except grpc.RpcError as e:
        raise HTTPException(
            status_code=400, detail=ErrorHanding._remove_data(e.details())
        )
    result = MessageToDict(response.transaction)

    if result and result is not None:
        for details in result["transactionDetails"]:
            try:
                if "value" in details:
                    value = ast.literal_eval(details["value"])
                    details["value"] = value
                else:
                    details["value"] = None
            except (ValueError, SyntaxError):
                pass
        return camel_to_snake._decode_keys(result)
    else:
        raise HTTPException(status_code=404, detail="Failed to get transaction!")


# Refund Process by settlement id
@router.post("/invoice-refund")
def full_invoice_refund_of_transaction(
    refund_details: RefundProcess,
    channel: t.Any = Depends(ConnectionChannel.grpc_payments_channel),
    dependencies=Depends(JWTBearer()),
) -> JSONResponse:
    client = (
        proto.payments_proto.transactions.transactions_pb2_grpc.TransactionServiceStub(
            channel
        )
    )
    try:
        grpc_request = (
            proto.payments_proto.transactions.transactions_pb2.RefundTransactionRequest(
                payment_method_type=refund_details.payment_method_type,
                transaction_id=refund_details.transaction_id,
                amount=refund_details.amount,
            )
        )
        response = client.RefundTransaction(grpc_request)

    except grpc.RpcError as e:
        raise HTTPException(
            status_code=400, detail=ErrorHanding._remove_data(e.details())
        )
    # print(response)
    response_data = json.loads(response.response)
    if response_data:
        return camel_to_snake._decode_keys(response_data)
    else:
        raise HTTPException(status_code=404, detail="Failed to refund transaction!")


# Get refund by refund id
@router.get("/refund/{refund_id:str}")
def get_refund_by_id(
    refund_id: str,
    channel: t.Any = Depends(ConnectionChannel.grpc_payments_channel),
    dependencies=Depends(JWTBearer()),
) -> JSONResponse:
    client = (
        proto.payments_proto.transactions.transactions_pb2_grpc.TransactionServiceStub(
            channel
        )
    )
    try:
        response = client.ReadRefund(
            proto.payments_proto.transactions.transactions_pb2.ReadRefundRequest(
                refund_id=refund_id
            )
        )
    except grpc.RpcError as e:
        raise HTTPException(
            status_code=400, detail=ErrorHanding._remove_data(e.details())
        )
    result = json.loads(response.response)

    if result:
        return camel_to_snake._decode_keys(result)
    else:
        raise HTTPException(status_code=404, detail="Failed to get refund!")


# Cancel refund by refund id
@router.put("/refund/{id:int}/cancel")
def cancel_refund_by_id(
    id: int,
    channel: t.Any = Depends(ConnectionChannel.grpc_payments_channel),
    dependencies=Depends(JWTBearer()),
) -> JSONResponse:
    client = (
        proto.payments_proto.transactions.transactions_pb2_grpc.TransactionServiceStub(
            channel
        )
    )

    try:
        grpc_request = (
            proto.payments_proto.transactions.transactions_pb2.CancelRefundRequest(
                id=id
            )
        )
        response = client.CancelRefund(grpc_request)
    except grpc.RpcError as e:
        raise HTTPException(
            status_code=400, detail=ErrorHanding._remove_data(e.details())
        )
    result = json.loads(response.response)

    if result:
        return result
    else:
        raise HTTPException(status_code=404, detail="Failed to cancel refund!")


# Get refunds by merchant reference number
@router.get("/refunds")
def get_refunds_by_merchant_reference_number(
    merchant_reference_number: str,
    channel: t.Any = Depends(ConnectionChannel.grpc_payments_channel),
    dependencies=Depends(JWTBearer()),
) -> JSONResponse:
    client = (
        proto.payments_proto.transactions.transactions_pb2_grpc.TransactionServiceStub(
            channel
        )
    )
    try:
        response = client.ListRefundsByMerchantReferenceNumber(
            proto.payments_proto.transactions.transactions_pb2.ListRefundsByMerchantReferenceNumberRequest(
                merchant_reference_number=merchant_reference_number
            )
        )
    except grpc.RpcError as e:
        raise HTTPException(
            status_code=400, detail=ErrorHanding._remove_data(e.details())
        )

    result = MessageToDict(response.refunds)

    return result


# Read refund by transaction id
@router.get("/{transaction_id:int}/refund")
def read_refund_by_transaction_id(
    transaction_id: int,
    channel: t.Any = Depends(ConnectionChannel.grpc_payments_channel),
    dependencies=Depends(JWTBearer()),
) -> JSONResponse:
    client = (
        proto.payments_proto.transactions.transactions_pb2_grpc.TransactionServiceStub(
            channel
        )
    )
    try:
        response = client.ReadRefundByTransactionId(
            proto.payments_proto.transactions.transactions_pb2.ReadRefundByTransactionIdRequest(
                transaction_id=transaction_id
            )
        )
    except grpc.RpcError as e:
        raise HTTPException(
            status_code=400, detail=ErrorHanding._remove_data(e.details())
        )

    result = MessageToDict(response.refund)

    return camel_to_snake._decode_keys(result)


# Transaction Listing
@router.get("/list")
def transaction_list(
    filter: t.Optional[str] = "",
    order_by: t.Optional[str] = "id",
    order_direction: t.Literal[
        OrderDirection.desc, OrderDirection.asc
    ] = OrderDirection.desc,
    payment_method_type: t.Literal[
        Type.paysafe, Type.authnet, Type.jupiter
    ] = Type.paysafe,
    user_id: t.Optional[int] = None,
    user_payment_method_id: t.Optional[int] = None,
    contact_payment_profile_id: t.Optional[int] = None,
    invoice_id: t.Optional[int] = None,
    page: t.Optional[int] = 1,
    limit: t.Optional[int] = 10,
    start_date: t.Optional[str] = None,
    end_date: t.Optional[str] = None,
    channel: t.Any = Depends(ConnectionChannel.grpc_payments_channel),
    dependencies=Depends(JWTBearer()),
) -> JSONResponse:
    client = (
        proto.payments_proto.transactions.transactions_pb2_grpc.TransactionServiceStub(
            channel
        )
    )
    try:
        grpc_request = (
            proto.payments_proto.transactions.transactions_pb2.ListTransactionsRequest(
                filter=filter,
                order_by=order_by,
                order_direction=order_direction,
                payment_method_type=payment_method_type,
                user_id=user_id,
                user_payment_method_id=user_payment_method_id,
                contact_payment_profile_id=contact_payment_profile_id,
                invoice_id=invoice_id,
                page=page,
                limit=limit,
                start_date=start_date,
                end_date=end_date,
            )
        )
        response = client.ListTransactions(grpc_request)

    except grpc.RpcError as e:
        raise HTTPException(
            status_code=400, detail=ErrorHanding._remove_data(e.details())
        )

    result = MessageToDict(response, including_default_value_fields=True)

    for transactionDetails in result["transactions"]:
        for detail in transactionDetails["transactionDetails"]:
            try:
                if "value" in detail:
                    value = ast.literal_eval(detail["value"])
                    detail["value"] = value
                else:
                    detail["value"] = None
            except (ValueError, SyntaxError):
                pass
    if result:
        return camel_to_snake._decode_keys(result)
    else:
        return {"message": "Failed to read data!"}, 404


# Read Settlement by transaction id
@router.get("/{transaction_id:int}/settlement")
def read_settlement_by_transaction_id(
    transaction_id: int,
    channel: t.Any = Depends(ConnectionChannel.grpc_payments_channel),
    dependencies=Depends(JWTBearer()),
) -> JSONResponse:
    client = (
        proto.payments_proto.transactions.transactions_pb2_grpc.TransactionServiceStub(
            channel
        )
    )
    try:
        response = client.ReadSettlementByTransactionId(
            proto.payments_proto.transactions.transactions_pb2.ReadSettlementByTransactionIdRequest(
                transaction_id=transaction_id
            )
        )
    except grpc.RpcError as e:
        raise HTTPException(
            status_code=400, detail=ErrorHanding._remove_data(e.details())
        )
    result = json.loads(response.settlement)
    return camel_to_snake._decode_keys(result)


# Partially Refund items of the invoice
@router.post("/partially-refund")
def partially_refund_invoice_items(
    refund_data: RefundTransaction,
    channel: t.Any = Depends(ConnectionChannel.grpc_payments_channel),
    d=Depends(JWTBearer()),
) -> JSONResponse:
    r = refund_data.refund_invoice.dict()
    client = (
        proto.payments_proto.transactions.transactions_pb2_grpc.TransactionServiceStub(
            channel
        )
    )
    try:
        grpc_request = proto.payments_proto.transactions.transactions_pb2.PartiallyRefundInvoiceItemsRequest(
            transaction_id=refund_data.transaction_id,
            refund_invoice=r,
        )
        response = client.PartiallyRefundInvoiceItems(grpc_request)
    except grpc.RpcError as e:
        raise HTTPException(
            status_code=400, detail=ErrorHanding._remove_data(e.details())
        )
    result = json.loads(response.response)
    result = camel_to_snake._decode_keys(result)

    return result
