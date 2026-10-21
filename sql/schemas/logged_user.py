from __future__ import annotations
from typing import List
from pydantic import BaseModel


class UserModel(BaseModel):
    id: int
    username: str
    roles: List[str]
    active: bool
