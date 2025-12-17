import logging

from fastapi import APIRouter, Request, Depends, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_login.exceptions import InvalidCredentialsException
from fastapi.responses import JSONResponse,PlainTextResponse
from sqlalchemy import desc, asc
import json

from .util import error
from .util import config
from .util import time_util
from . import api_webui
from . import db
from . import db_base
from . import db_imp
from . import models
from .util import security
from . import api_security
from datetime import datetime

LOGGING_ID = "api_native"
LOGGER = logging.getLogger(LOGGING_ID)

def jsonLoad(obj, fieldsRemove = []):

    j = json.loads(json.dumps(obj, cls=db_base.AlchemyEncoder))

    keys_to_remove = set(fieldsRemove).intersection(set(j.keys()))
    for key in keys_to_remove:
        del j[key]

    return j

router = APIRouter()

@router.post('/token')
async def token(request: Request):

    try:
        body = await request.json()

        if api_security.KEY_USERNAME not in body.keys() or api_security.KEY_PASSWORD not in body.keys():
            return error.get_error_json(error.ERROR_INVALID_PARAMETERS)

        username = body[api_security.KEY_USERNAME]
        password = body[api_security.KEY_PASSWORD]

        user = api_security.load_client_by_key(username)

        if not user:
            return JSONResponse(
                status_code=401,
                content={ "message": "Not Authenticated" },
            )
        elif not security.verify_password(password, user.get(api_security.KEY_PASSWORD_HASHED)):
            return JSONResponse(
                status_code=401,
                content={ "message": "Not Authenticated" },
            )

        access_token = api_security.getLoginManager().create_access_token(data=dict(sub={api_security.KEY_USERNAME: username}))

        return {'access_token': access_token, 'token_type': 'bearer'}
    except Exception as ex:
        LOGGER.error("AUTH request failed: " + str(ex))
        return error.get_error_json(error.ERROR_INTERNAL)

# @router.post("/activity")
# async def activity(request: Request, db_local: db_base.SessionLocal = Depends(db.get_model_db), user=Depends(api_security.getLoginManager())):

#     body = await request.json()
    
#     # if "name" not in body.keys():
#     #     return error.get_error_json(error.ERROR_INVALID_PARAMETERS)

#     a = db.get().get_athlete(user.get(api_security.KEY_USERNAME))

#     activities = []

#     if a is not None:
#         activities = db_local.query(models.Activity).filter(models.Activity.athlete_id == a.id)
#         # if name:
#         #     activities = activities.filter(models.Activity.name.like("%{}%".format(name)))
#         activities = activities.order_by(desc(models.Activity.time)).all()

#         json_array = []

#         keysRemove = ['child_hr', 'child_pwr', 'child_pwr_crv', 'source', 'source_hash', 'athlete_id', 'registry']

#         for activity in activities:
#             j = jsonLoad(activity, keysRemove) 
#             json_array.append(j)

#     return { 'results' : json_array }

# @router.post("/workout_search") #, response_class=PlainTextResponse)
# async def workout_search(request: Request, user=Depends(api_security.getLoginManager())):

#     duration = None
#     level = None 
#     zone = None

#     try:
#         body = await request.json()
#         if "duration" in body.keys():
#             duration = body['duration']
#         if "zone" in body.keys():
#             zone = body['zone']
#         if "level" in body.keys():
#             level = body['level']
#     except json.decoder.JSONDecodeError as ex:
#         return error.get_error_json(error.ERROR_INVALID_PARAMETERS)

#     workouts, desc = db.get().get_workouts_search(duration, zone, level)
    
#     json_array = [] 

#     keysRemove = ['source', 'source_hash','registry']

#     for w in workouts:
#         j = jsonLoad(w, keysRemove) 
#         json_array.append(j)

#     return { 'results' : json_array , 'desc' : desc }

@router.post("/transaction_groups") #, response_class=PlainTextResponse)
async def transaction_groups(request: Request, user=Depends(api_security.getLoginManager())):

    t_type= models.DB_T_TYPE_DEBIT_NORMAL

    try:
        body = await request.json()
        if "t_type" in body.keys():
            t_type = body['t_type']
    except json.decoder.JSONDecodeError as ex:
        return error.get_error_json(error.ERROR_INVALID_PARAMETERS)

    groups = db.get().get_transaction_groups(client=user.get(api_security.KEY_USERNAME), t_type=t_type)

    return { 'results' : groups }

@router.post("/transaction_classes") #, response_class=PlainTextResponse)
async def transaction_classes(request: Request, user=Depends(api_security.getLoginManager())):

    t_type= models.DB_T_TYPE_DEBIT_NORMAL
    t_group= None

    try:
        body = await request.json()
        if "t_type" in body.keys():
            t_type = body['t_type']
        if "t_group" in body.keys():
            t_group = body['t_group']
    except json.decoder.JSONDecodeError as ex:
        return error.get_error_json(error.ERROR_INVALID_PARAMETERS)

    classes = db.get().get_transaction_classes(client=user.get(api_security.KEY_USERNAME), t_type=t_type, t_group=t_group)

    return { 'results' : classes }

@router.post("/transaction_total") #, response_class=PlainTextResponse)
async def transaction_total(request: Request, user=Depends(api_security.getLoginManager())):

    period = time_util.START_12MONTHS 
    t_type= models.DB_T_TYPE_DEBIT_NORMAL

    try:
        body = await request.json()
        if "period" in body.keys():
            period = body['period']
        if "t_type" in body.keys():
            t_type = body['t_type']
    except json.decoder.JSONDecodeError as ex:
        return error.get_error_json(error.ERROR_INVALID_PARAMETERS)

    # transactions = db.get().get_transaction_group_summary(client=user.get(api_security.KEY_USERNAME), period=time_util.PERIOD_MONTH, start=period, t_type=t_type)
    transactions = db.get().get_transaction_group_total(client=user.get(api_security.KEY_USERNAME), start=period, t_type=t_type)

    total = 0
    for t in transactions:
        total += t[1]

    return { 'results' : transactions, 'total' : total}

@router.post("/transaction_summary") #, response_class=PlainTextResponse)
async def transaction_summary(request: Request, user=Depends(api_security.getLoginManager())):

    period = time_util.START_12MONTHS 
    t_type= models.DB_T_TYPE_DEBIT_NORMAL
    group_period=time_util.PERIOD_MONTH
    group_by = db_imp.Database.T_GROUP_BY_GROUP
    t_class = None
    t_group = None
    start_date = None;
    end_date = None;
    t_type_compare = None;

    try:
        body = await request.json()
        if "period" in body.keys():
            period = body['period']
        if "t_type" in body.keys():
            t_type = body['t_type']
        if "t_type_compare" in body.keys() and body['t_type_compare']:
            t = body['t_type_compare']
            if len(t) == 2:
                t_type_compare = t
            else:
                return error.get_error_json(error.ERROR_INVALID_PARAMETERS)
        if "group_period" in body.keys():
            group_period = body['group_period']
        if "t_class" in body.keys():
            t_class = body['t_class']
        if "t_group" in body.keys():
            t_group = body['t_group']
        if "group_by" in body.keys():
            group_by = body['group_by']
        if "start_date" in body.keys() and body['start_date']:
            start_date = datetime.strptime(body['start_date'], '%Y-%m-%d') 
        if "end_date" in body.keys() and body['end_date']:
            end_date = datetime.strptime(body['end_date'], '%Y-%m-%d') 
    except json.decoder.JSONDecodeError as ex:
        return error.get_error_json(error.ERROR_INVALID_PARAMETERS)

    if group_by is None:
        return error.get_error_json(error.ERROR_INVALID_PARAMETERS)

    if t_type_compare: # Compare 2 series
        # group by date only
        transactions_1 = db.get().get_transaction_summary(client=user.get(api_security.KEY_USERNAME), period=group_period, start=period, 
            group_by=None,t_type=t_type_compare[0], t_class=t_class, t_group=t_group, start_date=start_date, end_date=end_date)
        transactions_2 = db.get().get_transaction_summary(client=user.get(api_security.KEY_USERNAME), period=group_period, start=period, 
            group_by=None,t_type=t_type_compare[1], t_class=t_class, t_group=t_group, start_date=start_date, end_date=end_date)

        results = []
        for t1 in transactions_1:
            val = 0
            for t2 in transactions_2:
                if t1[0] == t2[0]:
                    val = t2[1]
                    break
            results.append((t1[0], val + t1[1]))

        total = 0
        for t in results:
            total += t[1]

        # print(transactions_1)
        # print(transactions_2)
        # print(results)

        return { 'results' : results, 'total' : total }
         
    else: # Normal
        transactions = db.get().get_transaction_summary(client=user.get(api_security.KEY_USERNAME), period=group_period, start=period, 
            group_by=group_by,t_type=t_type, t_class=t_class, t_group=t_group, start_date=start_date, end_date=end_date)
        total = 0
        for t in transactions:
            total += t[2]

        return { 'results' : transactions, 'total' : total }

@router.post("/transaction_search") #, response_class=PlainTextResponse)
async def transaction_search(request: Request, user=Depends(api_security.getLoginManager())):

    period = None;
    start_date = None;
    end_date = None;
    t_type= models.DB_T_TYPE_DEBIT_NORMAL
    t_class = None
    t_group = None
    value_gt = None
    value_lt = None

    try:
        body = await request.json()
        if "period" in body.keys():
            period = body['period']
        if "start_date" in body.keys() and body['start_date']:
            start_date = datetime.strptime(body['start_date'], '%Y-%m-%d') 
        if "end_date" in body.keys() and body['end_date']:
            end_date = datetime.strptime(body['end_date'], '%Y-%m-%d') 
        if "value_gt" in body.keys() and body['value_gt']:
            value_gt = body['value_gt']
        if "value_lt" in body.keys() and body['value_lt']:
            value_lt = body['value_lt']
        if "t_type" in body.keys():
            t_type = body['t_type']
        if "t_class" in body.keys():
            t_class = body['t_class']
        if "t_group" in body.keys():
            t_group = body['t_group']
    except json.decoder.JSONDecodeError as ex:
        return error.get_error_json(error.ERROR_INVALID_PARAMETERS)

    if period and start_date is None:
        start_date = time_util.get_start_date(period)

    transactions = db.get().get_transactions(client=user.get(api_security.KEY_USERNAME), start_date=start_date, end_date=end_date, 
        t_type=t_type, t_class=t_class, t_group=t_group, value_gt=value_gt, value_lt=value_lt)

    results = []
    for t in transactions:
        results.append(list(t))

    return { 'results' : results }


def get_router():
    return router