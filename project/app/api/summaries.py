# project/app/api/summaries.py


from fastapi import APIRouter, HTTPException, Path, BackgroundTasks
from fastapi import File, UploadFile, Depends
from typing import List, Dict
from uuid import UUID
from app.api import crud
from app.models.pydantic import (
    SummaryPayloadSchema,
    BulkSummaryPayloadSchema,
    SummaryResponseSchema,
    SummaryUpdatePayloadSchema,
    Job
)
from app.models.tortoise import SummarySchema
from app.summarizer import generate_summary, generate_bulk_summary

router = APIRouter()
jobs: Dict[UUID, Job] = {}


@router.post("/bulk", response_model=Job, status_code=202)
async def create_summary(
        background_tasks: BackgroundTasks, payload: BulkSummaryPayloadSchema = Depends(), file: UploadFile = File(...)
) -> SummaryResponseSchema:
    # logger.info("file " + file.filename)
    new_task = Job()
    jobs[new_task.uid] = new_task
    background_tasks.add_task(generate_bulk_summary, new_task, payload.modelName, file)
    return new_task


@router.post("/", response_model=SummaryResponseSchema, status_code=201)
async def create_summary(
        payload: SummaryPayloadSchema, background_tasks: BackgroundTasks
) -> SummaryResponseSchema:
    summary_id = await crud.post(payload)

    background_tasks.add_task(generate_summary, summary_id, payload.url)

    response_object = {"id": summary_id, "url": payload.url}
    return response_object


@router.get("/work/{id}/status", response_model=Job)
async def read_task(uid: UUID = Path(..., gt=0)) -> Job:
    return jobs[uid]


@router.get("/{id}/", response_model=SummarySchema)
async def read_summary(id: int = Path(..., gt=0)) -> SummarySchema:
    summary = await crud.get(id)
    if not summary:
        raise HTTPException(status_code=404, detail="Summary not found")

    return summary


@router.get("/", response_model=List[SummarySchema])
async def read_all_summaries() -> List[SummarySchema]:
    return await crud.get_all()


@router.delete("/{id}/", response_model=SummaryResponseSchema)
async def delete_summary(id: int = Path(..., gt=0)) -> SummaryResponseSchema:
    summary = await crud.get(id)
    if not summary:
        raise HTTPException(status_code=404, detail="Summary not found")

    await crud.delete(id)

    return summary


@router.put("/{id}/", response_model=SummarySchema)
async def update_summary(
        payload: SummaryUpdatePayloadSchema, id: int = Path(..., gt=0)
) -> SummarySchema:
    summary = await crud.put(id, payload)
    if not summary:
        raise HTTPException(status_code=404, detail="Summary not found")

    return summary
