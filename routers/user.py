# This module defines FastAPI routes for user-related operations in the payment API service.
# These routes handle user management, authentication, and profile updates through gRPC services.

import typing as t  # Type hints for better code documentation
import grpc, json  # gRPC communication and JSON processing
from fastapi import APIRouter, Depends, HTTPException  # FastAPI framework components
from fastapi.responses import JSONResponse  # JSON response handling
from google.protobuf.json_format import MessageToDict  # Convert protobuf messages to dictionaries
import proto.user_proto.user_user.user_user_pb2  # User protobuf definitions
import proto.user_proto.user_user.user_user_pb2_grpc  # User gRPC definitions
from helper.auth.auth_handler import JWTBearer  # JWT authentication handler
from helper.camel_to_snake import CamelToSnake  # Utility for case conversion
from helper.connection import ConnectionChannel  # gRPC connection management
from helper.error_handling import ErrorHanding  # Error handling utilities
from models.user import (
    UserUpdate,  # Model for updating user information
    UserPost,  # Model for creating new users
    UserUpdatePassword,  # Model for updating user passwords
    UserUpdateTimezone,  # Model for updating user timezone
)

camel_to_snake = CamelToSnake()  # Global instance for case conversion


router = APIRouter(
    prefix="/user",  # Base path for all user endpoints
    tags=["User"],  # OpenAPI tag for documentation
    responses={404: {"description": "Endpoint Not found"}},  # Default error response
)

# Create user 
@router.post("")
def post_user(
    user: UserPost,
    channel: t.Any = Depends(ConnectionChannel.grpc_user_channel),
    d: t.Any = Depends(JWTBearer()),
) -> JSONResponse:
    client = proto.user_proto.user_user.user_user_pb2_grpc.UserServiceStub(channel)
    r = camel_to_snake._decode_keys(user.dict())
    try:
        user = client.UserCreate(
            proto.user_proto.user_user.user_user_pb2.UserPostRequest(
                user=r
            )
        )
    except grpc.RpcError as e:
        raise HTTPException(
            status_code=400, detail=ErrorHanding._remove_data(e.details())
        )
    result = user.result  # MessageToDict(user.result)
    if result:
        return {"status": user.result, "message": user.message}
    else:
        raise HTTPException(status_code=400, detail=user.message)


# Find user details by id
@router.get("/{id:int}")
def single_user(
    id: int,
    channel: t.Any = Depends(ConnectionChannel.grpc_user_channel),
    d: t.Any = Depends(JWTBearer()),
) -> JSONResponse:
    client = proto.user_proto.user_user.user_user_pb2_grpc.UserServiceStub(channel)
    try:
        user = client.ReadUser(
            proto.user_proto.user_user.user_user_pb2.ReadUserRequest(id=id)
        )
    except grpc.RpcError as e:
        raise HTTPException(
            status_code=400, detail=ErrorHanding._remove_data(e.details())
        )
    result = MessageToDict(user.user, including_default_value_fields=True)
    if result:
        result = camel_to_snake._decode_keys(result)

        return result
    else:
        raise HTTPException(status_code=400, detail="User not found!")

# update user details
@router.put("/{id:int}")
def update_user(
    id: int,
    user: UserUpdate,
    channel: t.Any = Depends(ConnectionChannel.grpc_user_channel),
    d: t.Any = Depends(JWTBearer()),
) -> JSONResponse:
    user.id = id
    client = proto.user_proto.user_user.user_user_pb2_grpc.UserServiceStub(channel)
    r = camel_to_snake._decode_keys(user.dict())
    try:
        user = client.UpdateUser(
            proto.user_proto.user_user.user_user_pb2.UpdateUserRequest(user=r)
        )
    except grpc.RpcError as e:
        raise HTTPException(
            status_code=400, detail=ErrorHanding._remove_data(e.details())
        )
    result = MessageToDict(user.user, including_default_value_fields=True)
    if result:
        result = camel_to_snake._decode_keys(result)
        if "roles" in result:
            result["roles"] = result["roles"].split(",")
        if "invoice_post_review_invitation_ids" in result:
            result["invoice_post_review_invitation_ids"] = json.loads(
                result["invoice_post_review_invitation_ids"]
            )
        return result
    else:
        return {"message": "Failed to update!"}, 404

# update user's timezonne only
@router.put("/timezone/{id:int}")
def update_user_timezone(
    id: int,
    user: UserUpdateTimezone,
    channel: t.Any = Depends(ConnectionChannel.grpc_user_channel),
    d: t.Any = Depends(JWTBearer()),
) -> JSONResponse:
    client = proto.user_proto.user_user.user_user_pb2_grpc.UserServiceStub(channel)
    r = camel_to_snake._decode_keys(user.dict())
    try:
        user = client.UpdateUserTimezone(
            proto.user_proto.user_user.user_user_pb2.UpdateUserTimezoneRequest(
                id=id, timezone=r["timezone"]
            )
        )
    except grpc.RpcError as e:
        raise HTTPException(
            status_code=400, detail=ErrorHanding._remove_data(e.details())
        )
    result = MessageToDict(user.user, including_default_value_fields=True)
    if result:
        return camel_to_snake._decode_keys(result)
    else:
        return {"message": "Failed to update!"}, 404

# update user's password only
@router.put("/update-password/{id:int}")
def update_password_user(
    id: int,
    user: UserUpdatePassword,
    channel: t.Any = Depends(ConnectionChannel.grpc_user_channel),
    d: t.Any = Depends(JWTBearer()),
) -> JSONResponse:
    client = proto.user_proto.user_user.user_user_pb2_grpc.UserServiceStub(channel)
    r = camel_to_snake._decode_keys(user.dict())
    try:
        user = client.UpdateUserPassword(
            proto.user_proto.user_user.user_user_pb2.UpdateUserPasswordRequest(
                plain_password=r["plain_password"], id=id
            )
        )
    except grpc.RpcError as e:
        raise HTTPException(
            status_code=400, detail=ErrorHanding._remove_data(e.details())
        )
    result = user.result  # MessageToDict(user.result)
    if result:
        return {"status": user.result, "message": user.message}
    else:
        raise HTTPException(status_code=400, detail=user.message)

