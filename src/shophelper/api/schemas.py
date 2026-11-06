"""Request/response models for the HTTP API."""

from typing import Literal

from pydantic import BaseModel, Field, SecretStr


class ChatRequest(BaseModel):
    session_id: str = Field(
        min_length=8, max_length=64, pattern=r"^[A-Za-z0-9_-]+$",
        description="Client-generated conversation id; reuse it to continue a conversation.",
    )
    message: str = Field(min_length=1, max_length=2000)


class ApprovalRequest(BaseModel):
    session_id: str = Field(min_length=8, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
    approved: bool
    # Used only with accounts off (AWS). With accounts on, the reviewer is the signed-in user.
    reviewer: str = Field(default="support", min_length=1, max_length=64)
    note: str = Field(default="", max_length=500)


class SignupRequest(BaseModel):
    # Length and format are checked in auth.signup, to give a clear message. There is no role
    # field on purpose: unknown fields are dropped, so a request can't pick its own level.
    email: str
    password: SecretStr
    display_name: str = Field(default="", max_length=64)


class CartQuantity(BaseModel):
    quantity: int = Field(ge=0, le=10)  # 0 removes the item


class GuestCartItem(BaseModel):
    """Read from the browser, so it can hold anything. The merge rules deal with odd values."""

    product_id: int
    quantity: int


class CartMerge(BaseModel):
    items: list[GuestCartItem] = Field(max_length=100)


class LoginRequest(BaseModel):
    email: str
    password: SecretStr


class UserOut(BaseModel):
    id: int
    email: str
    role: Literal["customer", "support", "admin"]
    display_name: str


class RoleChange(BaseModel):
    role: Literal["customer", "support", "admin"]
