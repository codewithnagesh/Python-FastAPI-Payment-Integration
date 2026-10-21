import typing as t
import grpc
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from google.protobuf.json_format import MessageToDict
import proto.user_proto.user_user.user_user_pb2
import proto.user_proto.user_user.user_user_pb2_grpc
from helper.auth.auth_handler import JWTBearer
from helper.camel_to_snake import CamelToSnake
from helper.connection import ConnectionChannel
from helper.error_handling import ErrorHanding
from models.user import UserLogin

router = APIRouter(
    prefix="/login_check",
    tags=["Login"],
    responses={404: {"description": "Endpoint Not found"}},
)
camel_to_snake = CamelToSnake()


@router.post("")
def login(
    user_data: UserLogin,
    channel: t.Any = Depends(ConnectionChannel.grpc_user_channel),
) -> JSONResponse:
    client = proto.user_proto.user_user.user_user_pb2_grpc.UserServiceStub(channel)
    r = camel_to_snake._decode_keys(user_data.dict())
    try:
        user = client.UserLogin(
            proto.user_proto.user_user.user_user_pb2.UserLoginRequest(
                username=r["username"], password=r["password"]
            )
        )
    except grpc.RpcError as e:
        raise HTTPException(
            status_code=400, detail=ErrorHanding._remove_data(e.details())
        )
    user = camel_to_snake._decode_keys(
        MessageToDict(user, including_default_value_fields=True)
    )
    if "token" in user:
        return {"token": user["token"]}
    else:
        raise HTTPException(status_code=401, detail="Bad credentials")
