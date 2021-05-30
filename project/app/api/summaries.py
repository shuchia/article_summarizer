# project/app/api/summaries.py


from fastapi import APIRouter, HTTPException, Path, BackgroundTasks
from fastapi import File, UploadFile, Depends, Form
from fastapi.responses import HTMLResponse
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
from app.models.tortoise import SummarySchema, ReportSchema
from app.summarizer import generate_summary, generate_bulk_summary, generate_report
import os

router = APIRouter()
jobs: Dict[UUID, Job] = {}


@router.post("/bulk", response_model=Job, status_code=202)
async def create_summary(
        background_tasks: BackgroundTasks, modelname: str = Form(...), file: UploadFile = File(...)
) -> SummaryResponseSchema:
    # logger.info("file " + file.filename)
    new_task = Job()
    jobs[new_task.uid] = new_task
    payload = BulkSummaryPayloadSchema(modelName=modelname)
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


@router.get("/work/status", response_model=Job)
async def read_task(uid: UUID) -> Job:
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


@router.get("/task/{uid}/", response_model=List[SummarySchema])
async def read_all_summaries_for_a_task(uid: UUID) -> List[SummarySchema]:
    return await crud.get_all_for_a_task(uid)


@router.get("/generateReports", response_model=Dict[int, str], status_code=201)
async def generate_reports(uid: UUID) -> Dict[int, str]:
    return await generate_report(uid)


@router.get("/report/{id}/")
async def get_report(id: int = Path(..., gt=0)) -> HTMLResponse:
    report = await crud.getReport(id)
    # name = report["name"]
    report_content = report["report"]
    # file_path = os.getcwd() + "/" + name + ".html"
    return HTMLResponse(content=report_content, status_code=200)


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
