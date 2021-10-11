# project/app/models/pydantic.py
import json

from pydantic import BaseModel, AnyHttpUrl, Field
from uuid import UUID, uuid4
from typing import Dict


class BulkSummaryPayloadSchema(BaseModel):
    modelName: str

    @classmethod
    def __get_validators__(cls):
        yield cls.validate_to_json

    @classmethod
    def validate_to_json(cls, value):
        if isinstance(value, str):
            return cls(**json.loads(value))
        return value


class BaseSummarySchema(BaseModel):
    model_name: str
    length: str


class SummaryPayloadSchema(BaseSummarySchema):
    url: AnyHttpUrl


class TextSummaryPayloadSchema(BaseSummarySchema):
    text: str


class SummaryResponseSchema(SummaryPayloadSchema):
    id: int
    status: str
    task_id: UUID


class SummaryUpdatePayloadSchema(SummaryPayloadSchema):
    summary: str


class Job(BaseModel):
    uid: UUID = Field(default_factory=uuid4)
    status: str = "in_progress"
    processed_ids: Dict[int, str] = {}


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str = None


class User(BaseModel):
    username: str
    email: str = None
    full_name: str = None
    disabled: bool = None


class UserInDB(User):
    hashed_password: str
