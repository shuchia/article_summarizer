# project/app/api/summaries.py


from fastapi import APIRouter, HTTPException, Path, BackgroundTasks
from fastapi import File, UploadFile, Depends, Form
from fastapi.responses import HTMLResponse
from typing import List, Dict, Optional
import base64
from passlib.context import CryptContext
from datetime import datetime, timedelta
from starlette.responses import RedirectResponse, Response, JSONResponse

import jwt
from jwt import PyJWTError
from fastapi.security import OAuth2PasswordRequestForm, OAuth2
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
from starlette.status import HTTP_403_FORBIDDEN
from fastapi.encoders import jsonable_encoder

SECRET_KEY = "a9032cb3b87e7ad1d842e1a20fbf22901a2826d359a63ab6a6b6a8a7d1e9c019"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 180
fake_users_db = {
    "nsbharath": {
        "username": "nsbharath",
        "full_name": "NS Bharath",
        "email": "nsbharath@yahoo.com",
        "hashed_password": "Zmlwb2ludGVyMTIz",
        "disabled": False,
    }
}
basic_auth = BasicAuth(auto_error=False)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearerCookie(tokenUrl="/token")

router = APIRouter()
jobs: Dict[UUID, Job] = {}


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)


def authenticate_user(fake_db, username: str, password: str):
    user = get_user(fake_db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(*, data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=HTTP_403_FORBIDDEN, detail="Could not validate credentials"
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except PyJWTError:
        raise credentials_exception
    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@router.get("/")
async def homepage():
    return "Welcome to the security test!"


@router.post("/token", response_model=Token)
async def route_login_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/logout")
async def route_logout_and_remove_cookie():
    response = RedirectResponse(url="/")
    response.delete_cookie("Authorization", domain="ec2-54-152-94-32.compute-1.amazonaws.com")
    return response


@router.get("/login_basic")
async def login_basic(auth: BasicAuth = Depends(basic_auth)):
    if not auth:
        response = Response(headers={"WWW-Authenticate": "Basic"}, status_code=401)
        return response

    try:
        decoded = base64.b64decode(auth).decode("ascii")
        username, _, password = decoded.partition(":")
        user = authenticate_user(fake_users_db, username, password)
        if not user:
            raise HTTPException(status_code=400, detail="Incorrect email or password")

        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": username}, expires_delta=access_token_expires
        )

        token = jsonable_encoder(access_token)

        response = RedirectResponse(url="/docs")
        response.set_cookie(
            "Authorization",
            value=f"Bearer {token}",
            domain="ec2-54-152-94-32.compute-1.amazonaws.com",
            httponly=True,
            max_age=1800,
            expires=1800,
        )
        return response

    except:
        response = Response(headers={"WWW-Authenticate": "Basic"}, status_code=401)
        return response


@router.get("/openapi.json")
async def get_open_api_endpoint(current_user: User = Depends(get_current_active_user)):
    return JSONResponse(get_openapi(title="FastAPI", version=1, routes=router.routes))


@router.get("/docs")
async def get_documentation(current_user: User = Depends(get_current_active_user)):
    return get_swagger_ui_html(openapi_url="/openapi.json", title="docs")


@router.get("/users/me/", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user


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
