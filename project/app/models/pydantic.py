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


class SummaryPayloadSchema(BaseModel):
    url: AnyHttpUrl


class SummaryResponseSchema(SummaryPayloadSchema):
    id: int


class SummaryUpdatePayloadSchema(SummaryPayloadSchema):
    summary: str


class Job(BaseModel):
    uid: UUID = Field(default_factory=uuid4)
    status: str = "in_progress"
    processed_ids: Dict[int, str] = {}
