from __future__ import annotations
from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional


class PaymentType(str, Enum):
    authnet = "authnet"
    paysafe = "paysafe"
    jupiter = "jupiter"
    stripe = "stripe"
    paypal = "paypal"
    googlepay = "googlepay"
    applepay = "applepay"


class StatusType(str, Enum):
    approved = "approved"
    declined = "declined"
    pending = "pending"


class CreatePaymentApproval(BaseModel):
    user_id: int = None
    payment_method_type: PaymentType = Field(default=PaymentType.authnet)
    status: StatusType = Field(default=StatusType.pending)


class EditUserStatus(BaseModel):
    status: StatusType = Field(default=StatusType.pending)
    
class SendPaymentSetupDetails(BaseModel):
    username: str = None
    entity_type: str = None
    dba: str = None
    owner: str = None
    owner_name: str = None
    account: str = None