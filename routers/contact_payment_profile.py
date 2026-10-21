import typing as t

import grpc, json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from google.protobuf.json_format import MessageToDict

import proto.payments_proto.contact_payment_profile.contact_payment_profile_pb2
import proto.payments_proto.contact_payment_profile.contact_payment_profile_pb2_grpc
from helper.auth.auth_handler import JWTBearer
from helper.camel_to_snake import CamelToSnake
from helper.connection import ConnectionChannel
from helper.error_handling import ErrorHanding
from models.contact_payment_profile import ContactDetails
from models.user_payment_methods import OrderDirection, Type

camel_to_snake = CamelToSnake()


router = APIRouter(
    prefix="/contact-payment-profile",
    tags=["Contact Payment Profile"],
    responses={404: {"description": "Endpoint Not found"}},
)


# Create contact payment profile for all payment method
@router.post("/{payment_method}", status_code=201) 
def create_contact_payment_profile_for_payments(
    payment_method: t.Literal[Type.authnet, Type.paypal, Type.paysafe, Type.jupiter, Type.applepay, Type.googlepay],
    ContactDetails: ContactDetails,
    channel: t.Any = Depends(ConnectionChannel.grpc_payments_channel),
) -> JSONResponse:
    client = proto.payments_proto.contact_payment_profile.contact_payment_profile_pb2_grpc.ContactPaymentProfileServiceStub(
        channel
    )
    r = camel_to_snake._decode_keys(ContactDetails.dict())
    try:
        contact_profile = client.CreateContactProfile(
            proto.payments_proto.contact_payment_profile.contact_payment_profile_pb2.CreateContactProfileRequest(
                locale=r["locale"],
                payment_handle_token=r["payment_handle_token"],
                payment_type=r["payment_type"],
                amount=r["amount"],
                transaction_type=r["transaction_type"],
                payment_method=payment_method,
                card_number=r["card_number"],
                data_descriptor=r["data_descriptor"],
                data_value=r["data_value"],
                auth_pay_method=r["auth_pay_method"],
                invoice_id= r["invoice_id"],
            )
        )

    except grpc.RpcError as e:
        raise HTTPException(
            status_code=400, detail=ErrorHanding._remove_data(e.details())
        )

    result = json.loads(contact_profile.response)

    if result:
        return camel_to_snake._decode_keys(result)
    else:
        raise HTTPException(
            status_code=400, detail="Contact Payment Profile Failed to create!"
        )


# Get a payment profile
@router.get("/{id:int}")
def contact_payment_profile(
    id: int,
    channel: t.Any = Depends(ConnectionChannel.grpc_payments_channel),
    d: t.Any = Depends(JWTBearer()),
) -> JSONResponse:
    client = proto.payments_proto.contact_payment_profile.contact_payment_profile_pb2_grpc.ContactPaymentProfileServiceStub(
        channel
    )
    try:
        contact_payment_profile = client.ReadContactPaymentProfile(
            proto.payments_proto.contact_payment_profile.contact_payment_profile_pb2.ReadContactPaymentProfileRequest(
                id=id
            )
        )
    except grpc.RpcError as e:
        raise HTTPException(
            status_code=400, detail=ErrorHanding._remove_data(e.details())
        )

    result = MessageToDict(
        contact_payment_profile.profile, including_default_value_fields=True
    )
    if result:
        return camel_to_snake._decode_keys(result)
    else:
        raise HTTPException(
            status_code=400, detail="Contact Payment Profile record not found."
        )

# Get contact payment ppprfile information
@router.get("/contact/{id:int}")
def get_contact_payment_profile_by_user_id(
    id: int,
    channel: t.Any = Depends(ConnectionChannel.grpc_payments_channel),
    d: t.Any = Depends(JWTBearer()),
) -> JSONResponse:
    client = proto.payments_proto.contact_payment_profile.contact_payment_profile_pb2_grpc.ContactPaymentProfileServiceStub(
        channel
    )
    try:
        grpc_request = proto.payments_proto.contact_payment_profile.contact_payment_profile_pb2.ReadContactPaymentProfileByUserIdRequest(
            user_id=id
        )
        contact_payment_profile = client.ReadContactPaymentProfileByUserId(
            grpc_request
        )

    except grpc.RpcError as e:
        raise HTTPException(
            status_code=400, detail=ErrorHanding._remove_data(e.details())
        )

    result = MessageToDict(contact_payment_profile, including_default_value_fields=True)
    if result:
        return camel_to_snake._decode_keys(result)
    else:
        raise HTTPException(
            status_code=400, detail="Contact Payment Profile record not found."
        )

