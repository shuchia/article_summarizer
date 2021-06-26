# project/app/api/summaries.py

import httpx
from fastapi import APIRouter, HTTPException, Path, BackgroundTasks, status
from fastapi import File, UploadFile, Depends, Form, Header
from fastapi.responses import HTMLResponse
from typing import List, Dict, Optional

from starlette.responses import RedirectResponse, Response, JSONResponse

from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.openapi.docs import get_swagger_ui_html

from fastapi.openapi.utils import get_openapi

from uuid import UUID
from app.api import crud
from app.models.pydantic import (
    SummaryPayloadSchema,
    BulkSummaryPayloadSchema,
    SummaryResponseSchema,
    SummaryUpdatePayloadSchema,
    Job,
    BaseModel,
    TokenData,
    Token,
    UserInDB,
    User
)

from app.models.tortoise import SummarySchema, ReportSchema
from app.summarizer import generate_summary, generate_bulk_summary, generate_report
from app.oauth2 import BasicAuth, OAuth2PasswordBearerCookie

SECRET_KEY = "a9032cb3b87e7ad1d842e1a20fbf22901a2826d359a63ab6a6b6a8a7d1e9c019"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 180

security = HTTPBasic()

oauth2_scheme = OAuth2PasswordBearerCookie(tokenUrl="/token")

router = APIRouter()
jobs: Dict[UUID, Job] = {}


def has_access(credentials: HTTPBasicCredentials = Depends(security), authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='No access to resource. Credentials missing!',
        )
    headers = {'Authorization': authorization}
    result = httpx.get("http://ec2-54-152-94-32.compute-1.amazonaws.com:8002/api/access/auth", headers=headers)
    if result.status_code == 401:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='No access to resource. Login first.',
            headers={"WWW-Authenticate": "Basic"}
        )
        return result
    else:
        return result.json()


@router.get("/")
async def homepage():
    return "Welcome to the security test!"


@router.get("/openapi.json", dependencies=[Depends(has_access)])
async def get_open_api_endpoint():
    return JSONResponse(get_openapi(title="FastAPI", version=1, routes=router.routes))


@router.get("/docs", dependencies=[Depends(has_access)])
async def get_documentation():
    return get_swagger_ui_html(openapi_url="/openapi.json", title="docs")


@router.post("/bulk", response_model=Job, status_code=202, dependencies=[Depends(has_access)])
async def create_summary(
        background_tasks: BackgroundTasks, modelname: str = Form(...), file: UploadFile = File(...)
) -> SummaryResponseSchema:
    # logger.info("file " + file.filename)
    new_task = Job()
    jobs[new_task.uid] = new_task
    payload = BulkSummaryPayloadSchema(modelName=modelname)
    background_tasks.add_task(generate_bulk_summary, new_task, payload.modelName, file)
    return new_task


@router.post("/summary", response_model=SummaryResponseSchema, status_code=201)
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


@router.get("/summaries", response_model=List[SummarySchema])
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
