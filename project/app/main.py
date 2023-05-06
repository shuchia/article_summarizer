# project/app/main.py

import logging

from fastapi import FastAPI, Depends, HTTPException, status, Header
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi import APIRouter

import os

from app.api import ping, summaries
from app.db import init_db
from app.models.pydantic import (
    UserInDB,
    User)
import base64
from app.oauth2 import fake_users_db, get_user
from starlette.requests import Request
from starlette.responses import JSONResponse
from app.api.summaries import router as my_router

log = logging.getLogger(__name__)

security = HTTPBasic()
script_dir = os.path.dirname(__file__)
st_abs_file_path = os.path.join(script_dir, "static/")


def create_application() -> FastAPI:
    application = FastAPI()
    application.include_router(ping.router)
    application.include_router(
        summaries.router, prefix="/summaries", tags=["summaries"]
    )

    return application


def check_password(plain_password, hashed_password):
    decoded_pwd = base64.b64decode(hashed_password).decode("ascii")
    if plain_password == decoded_pwd:
        return True
    else:
        return False


def authenticate_user(fake_db, username: str, password: str):
    user = get_user(fake_db, username)
    # log.info(user.hashed_password)
    # log.info("unhashd pwd" + password)
    if not user:
        return False
    if not check_password(password, user.hashed_password):
        return False
    return user


# def create_access_token(*, data: dict, expires_delta: timedelta = None):
#     to_encode = data.copy()
#     if expires_delta:
#         expire = datetime.utcnow() + expires_delta
#     else:
#         expire = datetime.utcnow() + timedelta(minutes=15)
#     to_encode.update({"exp": expire})
#     encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
#     return encoded_jwt
#
#
# async def get_current_user(token: str = Depends(oauth2_scheme)):
#     credentials_exception = HTTPException(
#         status_code=HTTP_403_FORBIDDEN, detail="Could not validate credentials"
#     )
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         username: str = payload.get("sub")
#         if username is None:
#             raise credentials_exception
#         token_data = TokenData(username=username)
#     except PyJWTError:
#         raise credentials_exception
#     user = get_user(fake_users_db, username=token_data.username)
#     if user is None:
#         raise credentials_exception
#     return user
#
#
# async def get_current_active_user(current_user: User = Depends(get_current_user)):
#     if current_user.disabled:
#         raise HTTPException(status_code=400, detail="Inactive user")
#     return current_user

async def get_current_active_user(credentials: HTTPBasicCredentials = Depends(security)):
    user = get_user(fake_users_db, credentials.username)
    return user


def authorize(credentials: HTTPBasicCredentials = Depends(security)):
    # log.info(credentials.username, credentials.password)
    user = authenticate_user(fake_users_db, credentials.username, credentials.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Incorrect email or password.',
            headers={'WWW-Authenticate': 'Basic'},
        )


app = create_application()
app.mount("/static", StaticFiles(directory=st_abs_file_path), name="static")


def register_exception(app: FastAPI):
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        exc_str = f'{exc}'.replace('\n', ' ').replace('   ', ' ')
        # or logger.error(f'{exc}')
        log.error(request, exc_str)
        content = {'status_code': 10422, 'message': exc_str, 'data': None}
        return JSONResponse(content=content, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)


@app.on_event("startup")
async def startup_event():
    log.info("Starting up...")
    init_db(app)


@app.on_event("shutdown")
async def shutdown_event():
    log.info("Shutting down...")


@app.get('/')
async def root(request: Request):
    url = request.url_for('/summaries/reports', **request.query_params)
    return {'url': url}


@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    favicon_path = 'favicon.ico'
    return FileResponse(st_abs_file_path + favicon_path)


@app.get('/api/access/auth', dependencies=[Depends(authorize)])
def auth():
    return {"Granted": True}


@app.get('/api/access/auth/email')
def get_email(current_user: User = Depends(get_current_active_user)):
    return {"email": current_user.email}
