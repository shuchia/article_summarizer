# project/app/models/pydantic.py


from pydantic import BaseModel, AnyHttpUrl, Field
from uuid import UUID, uuid4
from typing import Dict


class BulkSummaryPayloadSchema(BaseModel):
    modelName: str


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
