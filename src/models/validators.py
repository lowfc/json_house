from datetime import datetime

from fastapi import HTTPException
from pydantic import BaseModel, validator


class TunedModel(BaseModel):
    class Config:
        orm_mode = True


class Response(TunedModel):
    error: bool = False
    error_code: int = 0
    message: str = ""
    data: dict | None


class BadResponse(Response):
    error: bool = True


# In models

class CreateRoom(BaseModel):
    type_id: int
    content: str
    name: str = ""
    headers: dict = {}
    require_parameters: dict = {}
    on_invalid_status_code: int = 200
    wait_microseconds: int = 0

    @validator("wait_microseconds")
    def validate_wait_microseconds(cls, value):
        if 0 > value > 4000:
            raise HTTPException(detail="wait_microseconds must be 0-4000", status_code=422)
        return value

    @validator("on_invalid_status_code")
    def validate_on_invalid_status_code(cls, value):
        if 599 < value < 0:
            raise HTTPException(detail="Invalid status code", status_code=422)
        return value

    @validator("type_id")
    def validate_type_id(cls, value):
        if value < 0:
            raise HTTPException(detail="invalid type", status_code=422)
        return value


class DeleteRoom(BaseModel):
    id: int

    @validator("id")
    def validate_id(cls, value):
        if value < 1:
            raise HTTPException(detail="invalid id", status_code=422)
        return value


# Out models


class ShowRoom(TunedModel):
    url: str
    id: int
    name: str
    content: str
    headers: dict
    content_type: dict
    require_parameters: dict
    on_invalid_status_code: int
    wait_microseconds: int
    created_at: datetime
    deleted_at: datetime
    deleted_at_unix: int


class RoomResponse(Response):
    data: ShowRoom


class AuthResponse(Response):
    data: str
