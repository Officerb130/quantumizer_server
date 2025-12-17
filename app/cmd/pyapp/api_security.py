import logging
import os
from .util import config
from .util import datadog
from fastapi import FastAPI, Request, Depends, BackgroundTasks

from fastapi.security import OAuth2PasswordRequestForm
from fastapi_login.exceptions import InvalidCredentialsException
from fastapi.responses import JSONResponse

from starlette.responses import Response
from starlette.responses import RedirectResponse
from starlette.responses import FileResponse
# import starlette.status as status

from typing import Optional
from fastapi import HTTPException, status

from . import db_base
from sqlalchemy import desc, asc
from . import models
from . import db
from . import db_imp
from datetime import date
from datetime import timedelta
from .util import security

LOGGING_ID = "api_security"
LOGGER = logging.getLogger(LOGGING_ID)

from fastapi_login import LoginManager

KEY_USERNAME="username"
KEY_PASSWORD="password"
KEY_PASSWORD_HASHED="password_hashed"

class InvalidLoginException(Exception):
    pass

# these two argument are mandatory
def InvalidLoginException_handler(request, exc):
    return RedirectResponse(url='/login')

class NotAuthenticatedException(Exception):
    pass

# these two argument are mandatory
def NotAuthenticatedException_handler(request, exc):
    return JSONResponse(
        status_code=401,
        content={ "message": "Not Authenticated" },
    )

    # return error.get_error_json(error.ERROR_AUTH)
    # return RedirectResponse(url='/login')

manager = LoginManager(config.get().ACCESS_DB_SECRET, token_url='/auth/token', use_cookie=True, 
    default_expiry=timedelta(seconds=config.get().ACCESS_TOKEN_EXPIRY_SECONDS), not_authenticated_exception=NotAuthenticatedException,
    cookie_name = "access_" + config.get().SERVICE_NAME )

# This will be deprecated in the future
# set your exception when initiating the instance
# manager = LoginManager(..., custom_exception=NotAuthenticatedException)
# manager.not_authenticated_exception = NotAuthenticatedException
# You also have to add an exception handler to your app instance

def load_client_by_key(name: str):
    user = None
    a = db.get().get_client(name) 
    if a is not None:
        user = { KEY_USERNAME : a.name, KEY_PASSWORD_HASHED : a.password_hashed }
    return user

@manager.user_loader()
def load_user(user_data: dict):  # could also be an asynchronous function
    return load_client_by_key(user_data.get(KEY_USERNAME))

def getLoginManager():
    return manager