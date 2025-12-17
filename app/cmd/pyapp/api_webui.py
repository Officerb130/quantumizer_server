import logging
import os
from .util import config
from .util import datadog
from .util import time_util
from .util import theme
from fastapi import FastAPI, Request, Depends, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from fastapi.security import OAuth2PasswordRequestForm
from fastapi_login.exceptions import InvalidCredentialsException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from starlette.responses import Response
from starlette.responses import RedirectResponse
from starlette.responses import FileResponse
# import starlette.status as status

from typing import Optional
from fastapi import HTTPException, status

from . import db_base
from . import api_native
import uvicorn
from pydantic import BaseModel 
from sqlalchemy import desc, asc
from . import models
from . import db
from . import db_imp
from . import api_security
from datetime import date
from datetime import timedelta
import random
from .util import custom_logging
from .util import security
from .util import key_killer
from pathlib import Path

LOGGING_ID = "api_webui"
LOGGER = logging.getLogger(LOGGING_ID)

def getLocalApp():
    l_app = FastAPI()

    config_path="logging_config.json"
    logger = custom_logging.CustomizeLogger.make_logger(config_path)
    l_app.logger = logger

    l_app.include_router(api_native.get_router(), prefix="/api")
    l_app.mount("/static", StaticFiles(directory="pyapp/static"), name="static")

    # TODO: Tighen origin?
    l_app.add_middleware(
        CORSMiddleware,
        allow_origins=['*'],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return l_app

app = getLocalApp()

folder = os.path.dirname(__file__)
template_folder = os.path.join(folder, 'templates')
template_folder = os.path.abspath(template_folder)
templates = Jinja2Templates(directory=template_folder)

app.add_exception_handler(api_security.InvalidLoginException, api_security.InvalidLoginException_handler)
# app.add_exception_handler(api_security.NotAuthenticatedException, api_security.NotAuthenticatedException_handler)

@app.exception_handler(api_security.NotAuthenticatedException)
def auth_exception_handler(request: Request, exc: api_security.NotAuthenticatedException):

    if request.method == "POST":
        return JSONResponse(
            status_code=401,
            content={ "message": "Not Authenticated" },
        )
    """
    Redirect the user to the login page if not logged in
    """
    return RedirectResponse(url='/login')

@app.post('/auth/token')
def login(data: OAuth2PasswordRequestForm = Depends()):

    access_token = None

    if len(config.get().DEFAULT_LOGIN_NAME) > 0 and api_security.load_client_by_key(config.get().DEFAULT_LOGIN_NAME):
        access_token = api_security.getLoginManager().create_access_token(data=dict(sub={api_security.KEY_USERNAME: config.get().DEFAULT_LOGIN_NAME}))
        response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
        response.set_cookie(key=api_security.getLoginManager().cookie_name, value=access_token, httponly=False)
        return response

    username = data.username
    password = data.password

    user = api_security.load_client_by_key(username)
    if not user:
        return RedirectResponse(url="/", status_code=status.HTTP_403_FORBIDDEN)
        # raise InvalidLoginException  # you can also use your own HTTPException
    elif not security.verify_password(password, user.get(api_security.KEY_PASSWORD_HASHED)):
        return RedirectResponse(url="/", status_code=status.HTTP_403_FORBIDDEN)

    access_token = api_security.getLoginManager().create_access_token(data=dict(sub={api_security.KEY_USERNAME: username}))

    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    response.set_cookie(key=api_security.getLoginManager().cookie_name, value=access_token, httponly=False)
    #api_security.getLoginManager().set_cookie(response, access_token)
    return response

    # return {'access_token': access_token, 'token_type': 'bearer'}

@app.get("/login")
def login(request: Request):
    return templates.TemplateResponse("login.html", {
        "request": request,
        "theme" : theme.get()
    })

@app.get("/logout")
async def route_logout_and_remove_cookie():
    response = RedirectResponse(url="/")
    api_security.getLoginManager().set_cookie(response, "")
    # response.delete_cookie("Authorization", domain="localtest.me")
    return response

favicon_path = 'pyapp/static/favicon.ico'

@app.get('/favicon.ico')
async def favicon():
    return FileResponse(favicon_path)

@app.get("/")
def home(request: Request, period="6 Months", user=Depends(api_security.getLoginManager())):

    summary = db.get().get_client_summary(user.get(api_security.KEY_USERNAME))
    
    summary['request'] = request
    summary['theme'] = theme.get()
    summary['period'] = period

    return templates.TemplateResponse("home.html", summary)

@app.get("/compare")
def compare(request: Request, user=Depends(api_security.getLoginManager())):

    summary = db.get().get_client_summary(user.get(api_security.KEY_USERNAME))

    summary['request'] = request
    summary['theme'] = theme.get()

    return templates.TemplateResponse("compare.html", summary)

@app.get("/transaction_search")
def transaction_search(request: Request, period = time_util.START_12MONTHS, value_lt = None, value_gt = None, t_type = None, user=Depends(api_security.getLoginManager())):

    start_date = time_util.get_start_date(period)

    transactions = db.get().get_transactions(client=user.get(api_security.KEY_USERNAME), start_date=start_date, value_lt=value_lt, value_gt=value_gt, t_type=t_type)

    return templates.TemplateResponse("transaction_search.html", {
        "request": request, 
        "transactions": transactions, 
        "period" : period,
        "value_lt" : value_lt,
        "value_gt" : value_gt,
        "t_type" : t_type,  
        "theme" : theme.get()
    })

@app.get("/transaction_summary")
def transaction_summary(request: Request, period = time_util.START_12MONTHS, t_type=models.DB_T_TYPE_DEBIT_NORMAL, user=Depends(api_security.getLoginManager())):

    return templates.TemplateResponse("transaction_summary.html", {
        "request": request, 
        "period" : period,
        "t_type" : t_type,
        "theme" : theme.get()
    })

def getApp():
    return app

# BG Task Example
# @app.post("/stock")
# async def create_stock(stock_request: StockRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
#     """
#     add one or more tickers to the database
#     background task to use yfinance and load key statistics
#     """

#     stock = Stock()
#     stock.symbol = stock_request.symbol
#     db.add(stock)
#     db.commit()

#     background_tasks.add_task(fetch_stock_data, stock.id)

#     return {
#         "code": "success",
#         "message": "stock was added to the database"
#     }

