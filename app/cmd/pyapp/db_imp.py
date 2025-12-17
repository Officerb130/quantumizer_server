import logging
import json

from .util import config
from .util import time_util
import sqlite3
from . import db_base
from . import db
from . import models
from .util import cache_helper
from .util import security
import pandas as pd
import re
from datetime import datetime, timedelta

from sqlalchemy import func, join, select
from sqlalchemy import desc, asc, func
from sqlalchemy.orm import Session

LOGGING_ID = "Database"
LOGGER = logging.getLogger(LOGGING_ID)

###################################################
# Database

class classify_checker:
    def __init__(self, cid, cf):
        cf['regex'] = cf['regex'].upper()
        self.regex = re.compile(cf['regex'])
        self.value = cf['value'] if 'value' in cf.keys() else None
        self.value_max = cf['value_max'] if 'value_max' in cf.keys() else None
        self.value_min = cf['value_min'] if 'value_min' in cf.keys() else None
        self.date = cf['date'] if 'date' in cf.keys() else None
        self.cid = cid

    # Case insensitive (upper)
    def check(self, description, amount, date):
        description = description.upper()
        if self.regex.match(description):
            if self.value and amount != self.value:
                return None
            if self.date and date != self.date:
                return None
            if self.value_max and abs(amount) > self.value_max:
                return None
            if self.value_min and abs(amount) < self.value_min:
                return None
            return self.cid
        return None
    
    def getKey(self):
        return self.regex

class Database(db_base.DatabaseBase):
    def __init__(self):
        self.db_filename = db_base.SQL_DB_FILE
        self.init_db_defaults()
        
    def get_row_count(self, table, filter = None):
        db_records = 0
        with sqlite3.connect(self.db_filename) as conn:
            cursor = conn.cursor()
            q = 'select count(*) from {}'.format(table)
            if filter:
                q = q + " where " + filter
            cursor.execute(q)
            for row in cursor.fetchall():
                db_records = row[0]
        return db_records

    def __delete_records(self, table, filter = None):
        with sqlite3.connect(self.db_filename) as conn:
            cursor = conn.cursor()
            q = 'delete from {}'.format(table)
            if filter:
                q = q + " where " + filter
            cursor.execute(q)
        
    def init_db_defaults(self):

        LOGGER.info("Checking DB Defaults")

        if self.get_row_count('client') == 0:

            default_json = "{}/general/{}".format(config.get().DATA_FOLDER, 'client_defaults.json')
            try:
                with open(default_json, 'r') as f:
                    j = json.load(f)
                    if 'clients' in j:
                        for a in j['clients']:
                            name, ctype = a['name'], a['type']
                            password_hashed = security.get_password_hash(a['password'])

                            row_id = None
        
                            # Core record
                            with sqlite3.connect(self.db_filename) as conn:
                                q = 'insert into client (name, password_hashed, type) values("{}", "{}", "{}")'.format(name, password_hashed, ctype)
                                cursor=conn.cursor()
                                cursor.execute(q)
                                row_id = cursor.lastrowid

                            LOGGER.info("Added client to DB (Name: {}, ID: {})".format(name, row_id))
            except (ValueError, OSError) as ex:
                LOGGER.error("Error in dbinit -> {}".format(str(ex)))
                pass
            except (KeyError) as ex:
                LOGGER.error("Key Error in db_defaults.json -> {}".format(str(ex)))
                pass

        self.sync_db_classes()

    def sync_db_classes(self):

        LOGGER.info("Sync all classes...")

        # self.__delete_records("client_transaction_to_class")
        self.__delete_records("client_transaction_class")
        self.__delete_records("client_transaction_group")
        self.__delete_records("client_transaction_type")

        default_json = "{}/general/{}".format(config.get().DATA_FOLDER, 'type_defaults.json')
        try:
            with open(default_json, 'r') as f:
                j = json.load(f)
                count = 0
                if 'type' in j:
                    for a in j['type']:
                        name, hidden = a['name'], a['hidden']
                        row_id = None

                        # Core record
                        with sqlite3.connect(self.db_filename) as conn:
                            q = 'insert into client_transaction_type (name, hidden) \
                                values("{}", {})'.format(name, hidden)
                            cursor=conn.cursor()
                            cursor.execute(q)
                            row_id = cursor.lastrowid

                        count += 1

                        LOGGER.debug("Added type to DB (Name: {}, ID: {})".format(name, row_id))

                LOGGER.info("Added {} transaction types to DB".format(count))
        except (ValueError, OSError) as ex:
            LOGGER.error("Error in type dbinit -> {}".format(str(ex)))
            pass
        except (KeyError) as ex:
            LOGGER.error("Key Error in type_defaults.json -> {}".format(str(ex)))
            pass

        default_json = "{}/general/{}".format(config.get().DATA_FOLDER, 'group_defaults.json')
        try:
            with open(default_json, 'r') as f:
                j = json.load(f)
                count = 0
                if 'group' in j:
                    for a in j['group']:
                        name = a['name']

                        row_id = None

                        # Core record
                        with sqlite3.connect(self.db_filename) as conn:
                            q = 'insert into client_transaction_group (name) \
                                values("{}")'.format(name)
                            cursor=conn.cursor()
                            cursor.execute(q)
                            row_id = cursor.lastrowid

                        count += 1

                        LOGGER.debug("Added group to DB (Name: {}, ID: {})".format(name, row_id))

                LOGGER.info("Added {} transaction groups to DB".format(count))
        except (ValueError, OSError) as ex:
            LOGGER.error("Error in group dbinit -> {}".format(str(ex)))
            pass
        except (KeyError) as ex:
            LOGGER.error("Key Error in group_defaults.json -> {}".format(str(ex)))
            pass

        try:
            with open(self.getClassFilename(), 'r') as f:
                j = json.load(f)
                count = 0
                if 'class' in j:
                    for a in j['class']:
                        name, group= a['name'], a['group']

                        t_type = models.DB_T_TYPE_DEBIT_NORMAL
                        if 'type' in a.keys():
                            t_type = a['type']

                        group_o = self.get_transaction_group(group)
                        group_id = None

                        if group_o:
                            group_id = group_o.id
                        else:
                            LOGGER.error("Group name not found -> {} (class = {})".format(group, name))
                            continue
        
                        type_o = self.get_transaction_type(t_type)
                        type_id = None

                        if type_o:
                            type_id = type_o.id
                        else:
                            LOGGER.error("Type not found -> {} (class = {})".format(t_type, name))
                            continue

                        row_id = None
        
                        # Core record
                        with sqlite3.connect(self.db_filename) as conn:
                            q = 'insert into client_transaction_class (name, group_id, type_id) \
                                values("{}", {}, {})'.format(name, group_id, type_id)
                            cursor=conn.cursor()
                            cursor.execute(q)
                            row_id = cursor.lastrowid

                        count += 1

                        LOGGER.debug("Added class to DB (Name: {}, ID: {})".format(name, row_id))

                LOGGER.info("Added {} transaction classes to DB".format(count))

        except (ValueError, OSError) as ex:
            LOGGER.error("Error in class dbinit -> {}".format(str(ex)))
            pass
        except (KeyError) as ex:
            LOGGER.error("Key Error in class_defaults.json -> {}".format(str(ex)))
            pass

        self.classify_transaction(start_time = time_util.get_start_date(time_util.START_24MONTHS))
        #self.classify_transaction(start_time = time_util.get_start_date(time_util.START_ALL))

    def getClassFilename(self):
        return "{}/general/{}".format(config.get().DATA_FOLDER, 'class_defaults.json')

    def get_classifiers(self):

        classifiers = []
        try:
            with open(self.getClassFilename(), 'r') as f:
                j = json.load(f)
                if 'class' in j:
                    for a in j['class']:
                        c = self.get_transaction_class(a['name'])
                        if c is None:
                            LOGGER.error("Failed to find class -> {}".format(a['name']))
                            continue
                        classifier_objs = []
                        for c_json in a['classifiers']:
                            classifier_objs.append(classify_checker(c.id,c_json))
                        if c:
                            classifiers.append( { 'classid' : c.id, 'classifiers' : classifier_objs })
        except (ValueError, OSError) as ex:
            LOGGER.error("Error in dbinit -> {}".format(str(ex)))
            pass
        except (KeyError) as ex:
            LOGGER.error("Key Error in class_defaults.json -> {}".format(str(ex)))
            pass
            
        return classifiers



    def classify_transaction(self, start_time):

        dt = time_util.DurationTimer()

        LOGGER.info("Begin Classify Transactions Since {}...".format(start_time))

        classifiers = self.get_classifiers()
        transactions = self.get_transactions_raw(start_date=start_time)

        undefined_debit = self.get_transaction_class(models.UNDEFINED_DEBIT)
        undefined_credit = self.get_transaction_class(models.UNDEFINED_CREDIT)

        if undefined_debit is None or undefined_credit is None:
            LOGGER.error("No undefined classes found")
            return

        count = 0

        lru = cache_helper.SimpleLRUCache(200)

        # Just match first...
        for t in transactions:
            id = t[0]
            date =  t[1].strftime('%Y-%m-%d')
            description = t[2]
            # Remove the double spaces..
            description = re.sub(r'\s+' , ' ', description)
            amount = t[3]
            targetClass = undefined_debit.id if amount < 0 else undefined_credit.id

            # Search LRU first
            iter_pos = 0
            for key in lru.get_cache():
                value = lru.getNoPop(key)
                tClass = value.check(description, amount, date)
                if tClass:
                    targetClass = tClass
                    lru.put(value.getKey(), value)
                    #LOGGER.info("Cache Hit ({}, {})".format(value.getKey(), iter_pos))
                    break
                iter_pos += 1

            # bCheck = False
            # if description.find("DAVIDS") != -1:
            #     bCheck = True
            #     LOGGER.info("CHECK: " + description)

            # Search all
            if targetClass in [undefined_debit.id, undefined_credit.id]:

                 # Search exact matches
                for c in classifiers:
                    class_finders = c['classifiers']
                   
                    for cf in class_finders:
                        if cf.date is None and cf.value is None:
                            continue
                        # LOGGER.info("Check class ({} -> {})".format(description, cf.getKey()))
                        tClass = cf.check(description, amount, date)
                        if tClass:
                            targetClass = tClass
                            # LOGGER.info("Match class ({} -> {})".format(description, cf.getKey()))
                            lru.put(cf.getKey(), cf)
                            break
                    if targetClass not in [undefined_debit.id, undefined_credit.id]:
                        break

                # Search partial matches
                if targetClass in [undefined_debit.id, undefined_credit.id]:
                    for c in classifiers:
                        class_finders = c['classifiers']
                        for cf in class_finders:
                            if cf.date is not None and cf.value is not None:
                                continue
                            # LOGGER.info("Check class ({} -> {})".format(description, cf.getKey()))
                            tClass = cf.check(description, amount, date)
                            if tClass:
                                targetClass = tClass
                                # LOGGER.info("Match class ({} -> {})".format(description, cf.getKey()))
                                lru.put(cf.getKey(), cf)
                                break

                        if targetClass not in [undefined_debit.id, undefined_credit.id]:
                            break

            # if bCheck:
            #     LOGGER.info("Target: " + str(targetClass))

            # Update DB
            with sqlite3.connect(self.db_filename) as conn:
                q = 'update client_transaction set class_id = {} where id = {}'.format(targetClass, id)
                cursor=conn.cursor()
                cursor.execute(q)
                count += 1

        LOGGER.info("Classified {} Transactions ({})".format(count, dt))

    def get_transaction(self, transdate, description, amount, source):

        source_rec = self.get_transaction_source(source)

        if source_rec is None:
            return None

        for c in db.get_model_db():
            d = c.query(models.ClientTransaction)
            s = d.filter(models.ClientTransaction.date == transdate).\
                filter(models.ClientTransaction.description == description).\
                filter(models.ClientTransaction.amount == amount).\
                filter(models.ClientTransaction.source_id == source_rec.id).\
                first()
            return s
        return None

    def get_transactions_raw(self, client = None, start_date = None, end_date = None):
    
        for c in db.get_model_db():

            d = select(models.ClientTransaction.id, models.ClientTransaction.date,models.ClientTransaction.description, models.ClientTransaction.amount)

            if start_date:
                d = d.filter(models.ClientTransaction.date >= start_date)

            if end_date:
                d = d.filter(models.ClientTransaction.date < end_date)

            d = d.order_by(desc(models.ClientTransaction.date))

            return Session(db.get_model_engine()).execute(d)

        return None

    def get_transactions(
        self,
        client=None,
        start_date=None,
        end_date=None,
        t_type=None,
        t_class=None,
        t_group=None,
        value_lt=None,
        value_gt=None,
        include_hidden=True
    ):
        cli = self.get_client(client)
        type_filter = self.get_transaction_type(t_type)
        class_filter = self.get_transaction_class(t_class)
        group_filter = self.get_transaction_group(t_group)
        cli = self.get_client(client)
        
        for c in db.get_model_db():

            d = select(models.ClientTransaction.id, models.ClientTransaction.date,models.ClientTransaction.description, 
            models.ClientTransaction.amount, models.ClientTransactionClass.name.label('Class'), models.ClientTransactionGroup.name.label('Group'),
            models.ClientTransactionSource.name.label('Source'), models.ClientTransactionType.name.label('Type'))\
            .join(models.ClientTransactionClass, models.ClientTransactionClass.id==models.ClientTransaction.class_id)\
            .join(models.ClientTransactionGroup).join(models.ClientTransactionSource).join(models.ClientTransactionType)

            if start_date:
                d = d.filter(models.ClientTransaction.date >= start_date)

            if end_date:
                d = d.filter(models.ClientTransaction.date <= end_date)

            if type_filter:
                d = d.filter(models.ClientTransactionType.id == type_filter.id)

            if group_filter:
                d = d.filter(models.ClientTransactionGroup.id == group_filter.id)

            if class_filter:
                d = d.filter(models.ClientTransactionClass.id == class_filter.id)

            if cli:
                d = d.filter(models.ClientTransactionSource.client_id ==  cli.id)
                
            if value_gt:
                d = d.filter(func.abs(models.ClientTransaction.amount) > int(value_gt))
                
            if value_lt:
                d = d.filter(func.abs(models.ClientTransaction.amount) < int(value_lt))
                
            if not include_hidden:
                d = d.filter(models.ClientTransactionType.hidden == 0)

            d = d.order_by(desc(models.ClientTransaction.date))

            return Session(db.get_model_engine()).execute(d).all()

        return None

    def insert_transaction(self, transdate, description, amount, source, source_type, client):

        #amount = int(round(amount,0))

        if self.get_transaction(transdate, description, amount, source) is not None:
            return None

        source_rec = self.get_create_transaction_source(source,source_type,client)

        # Core record
        with sqlite3.connect(self.db_filename) as conn:
            q = 'insert into client_transaction (date, description, amount, source_id) \
                values("{}", "{}", {}, {})'.format(transdate, description, amount, source_rec.id)
            cursor=conn.cursor()
            cursor.execute(q)
            return cursor.lastrowid

        return None

    def get_transaction_file_source(self, name, client):

        cli = self.get_client(client)
        
        for c in db.get_model_db():
            d = c.query(models.ClientTransactionSourceFile)
            s = d.filter(models.ClientTransactionSourceFile.name == name).\
                filter(models.ClientTransactionSourceFile.client_id == cli.id).\
                first()
            if s is not None:
                return s
        return None

    def insert_update_transaction_source_file(self, filename, client, data_hash):
    
        cli = self.get_client(client)

        # Remove
        with sqlite3.connect(self.db_filename) as conn:
            q = 'delete from client_transaction_source_file where name = "{}" and client_id = {}'.format(filename, cli.id)
            cursor=conn.cursor()
            cursor.execute(q)

        # Add
        with sqlite3.connect(self.db_filename) as conn:
            q = 'insert into client_transaction_source_file (name, data_hash, client_id) \
                values("{}", "{}", {})'.format(filename, data_hash, cli.id)
            cursor=conn.cursor()
            cursor.execute(q)
            return cursor.lastrowid

        return None

    def get_transaction_type(self, name):
        if name is None:
            return None
        for c in db.get_model_db():
            d = c.query(models.ClientTransactionType)
            s = d.filter(models.ClientTransactionType.name == name).first()
            if s is not None:
                return s
        return None

    def get_transaction_source(self, name):
        if name is None:
            return None
        for c in db.get_model_db():
            d = c.query(models.ClientTransactionSource)
            s = d.filter(models.ClientTransactionSource.name == name).first()
            if s is not None:
                return s
        return None

    def get_create_transaction_source(self, name, type, client):

        cli = self.get_client(client)

        for c in db.get_model_db():
            d = c.query(models.ClientTransactionSource)
            s = d.filter(models.ClientTransactionSource.name == name).first()
            if s is not None:
                return s

        with sqlite3.connect(self.db_filename) as conn:
            q = 'insert into client_transaction_source (name, type, client_id) \
                values("{}", "{}", {})'.format(name, type, cli.id)
            cursor=conn.cursor()
            cursor.execute(q)
        
        for c in db.get_model_db():
            d = c.query(models.ClientTransactionSource)
            return d.filter(models.ClientTransactionSource.name == name).first()

        return None

    def get_transaction_class(self, name):
        if name is None:
            return None
        for c in db.get_model_db():
            d = c.query(models.ClientTransactionClass)
            return d.filter(func.lower(models.ClientTransactionClass.name) == func.lower(name)).first()
        return None

    def get_transaction_group(self, name):
        if name is None:
            return None
        for c in db.get_model_db():
            d = c.query(models.ClientTransactionGroup)
            return d.filter(func.lower(models.ClientTransactionGroup.name) == func.lower(name)).first()
        return None

    def get_client(self, name):
        if name is None:
            return None
        for c in db.get_model_db():
            client = c.query(models.Client)
            return client.filter(func.lower(models.Client.name) == func.lower(name)).first()
        return None

    def get_clients(self):
        for c in db.get_model_db():
            return c.query(models.Client).all()
        return None

    def get_transaction_groups(self, client, t_type):
        
        t_client = self.get_client(client)
        trans_type = self.get_transaction_type(t_type)

        if t_client is None:
            return []

        ret = []
        if client is not None:
            with sqlite3.connect(self.db_filename) as conn:
                cursor = conn.cursor()
                q="SELECT distinct(t3.name) \
                FROM client_transaction t1 \
                JOIN client_transaction_class t2 ON t1.class_id = t2.id \
                JOIN client_transaction_group t3 ON t2.group_id = t3.id \
                JOIN client_transaction_source t4 ON t1.source_id = t4.id \
                JOIN client_transaction_type t5 ON t2.type_id = t5.id \
                where t4.client_id = {} and t5.id = {} \
                order by t3.name".format(t_client.id, trans_type.id)
                cursor.execute(q)
                for row in cursor.fetchall():
                    ret.append(row[0])
        return ret

    def get_transaction_classes(self, client, t_type, t_group):
        
        t_client = self.get_client(client)
        trans_type = self.get_transaction_type(t_type)
        t_group_c = self.get_transaction_group(t_group)

        if t_client is None:
            return []

        ret = []
        if client is not None:
            with sqlite3.connect(self.db_filename) as conn:
                cursor = conn.cursor()
                q="SELECT distinct(t2.name) \
                FROM client_transaction t1 \
                JOIN client_transaction_class t2 ON t1.class_id = t2.id \
                JOIN client_transaction_group t3 ON t2.group_id = t3.id \
                JOIN client_transaction_source t4 ON t1.source_id = t4.id \
                JOIN client_transaction_type t5 ON t2.type_id = t5.id \
                where t4.client_id = {} and t5.id = {}".format(t_client.id, trans_type.id)

                if t_group_c:
                    q += " and t3.id = {}".format(t_group_c.id)

                q += " order by t2.name"

                cursor.execute(q)
                for row in cursor.fetchall():
                    ret.append(row[0])
        return ret

    def get_transaction_group_total(self, client, start, t_type):
        
        start_date = time_util.get_start_date(start)
        t_client = self.get_client(client)
        trans_type = self.get_transaction_type(t_type)

        if t_client is None:
            return []
        
        if start_date is None:
            start_date = datetime.today() + timedelta(days=-10000)

        ret = []
        if client is not None:
            with sqlite3.connect(self.db_filename) as conn:
                cursor = conn.cursor()
                q="SELECT t3.name, sum(t1.amount) \
                FROM client_transaction t1 \
                JOIN client_transaction_class t2 ON t1.class_id = t2.id \
                JOIN client_transaction_group t3 ON t2.group_id = t3.id \
                JOIN client_transaction_source t4 ON t1.source_id = t4.id \
                JOIN client_transaction_type t5 ON t2.type_id = t5.id \
                where t4.client_id = {} and t1.date >= datetime('{}') and t5.id = {} \
                group by t3.name order by t3.name".format(t_client.id, start_date.strftime("%Y-%m-%d %H:%M:%S"), trans_type.id)
                cursor.execute(q)
                for row in cursor.fetchall():
                    ret.append((row[0], row[1]))
        return ret

    T_GROUP_BY_GROUP = "group"
    T_GROUP_BY_CLASS = "class"

    def get_transaction_summary(self, client, period, start, group_by, t_type = models.DB_T_TYPE_DEBIT_NORMAL, t_group = None, 
        t_class = None, start_date= None, end_date=None, include_hidden=True):
        
        if start and start_date is None:
            start_date = time_util.get_start_date(start)

        group_by_format = time_util.get_period_format(period)
        trans_type = self.get_transaction_type(t_type)
        trans_group = self.get_transaction_group(t_group)
        trans_class = self.get_transaction_class(t_class)
        client = self.get_client(client)

        group_by_param = None

        if group_by == Database.T_GROUP_BY_GROUP:
            group_by_param = "t3.name"
        elif group_by == Database.T_GROUP_BY_CLASS:
            group_by_param = "t2.name"

        ret = []
        if client is not None:
            with sqlite3.connect(self.db_filename) as conn:
                cursor = conn.cursor()
                q=""
                if group_by_param:
                    q += "SELECT {}, strftime('{}', t1.date), sum(t1.amount)".format(group_by_param, group_by_format)
                else:
                     q += "SELECT strftime('{}', t1.date), sum(t1.amount)".format(group_by_format)

                q += " FROM client_transaction t1 \
                JOIN client_transaction_class t2 ON t1.class_id = t2.id \
                JOIN client_transaction_group t3 ON t2.group_id = t3.id \
                JOIN client_transaction_source t4 ON t1.source_id = t4.id \
                JOIN client_transaction_type t5 ON t2.type_id = t5.id \
                where t4.client_id = {} and t5.id = {}".format(client.id, trans_type.id)
                

                if start_date:
                    q += " and t1.date >= datetime('{}')".format(start_date.strftime("%Y-%m-%d %H:%M:%S"))

                if end_date:
                    q += " and t1.date <= datetime('{}')".format(end_date.strftime("%Y-%m-%d %H:%M:%S"))

                if trans_group:
                    q += " and t3.id = {}".format(trans_group.id)

                if trans_group:
                    q += " and t3.id = {}".format(trans_group.id)

                if trans_class:
                    q += " and t2.id = {}".format(trans_class.id)
                    
                if not include_hidden:
                    q += " and t5.hidden = 0"

                if group_by_param:
                    q +=" group by {}, strftime('{}', t1.date) order by strftime('{}', t1.date)".format(group_by_param, group_by_format, group_by_format)
                else:
                    q +=" group by strftime('{}', t1.date) order by strftime('{}', t1.date)".format(group_by_format, group_by_format)

                cursor.execute(q)
                for row in cursor.fetchall():
                    if group_by_param:
                        ret.append((row[0], row[1], row[2]))
                    else:
                        ret.append((row[0], row[1]))
        return ret
    
    def get_client_summary(self, name):
        return { "spend_week" : 100, "spend_month" : 100 }


    #     return None

    # def get_athletes(self):
    #     for c in db.get_model_db():
    #         return c.query(models.Athlete).all()
    #     return None

    # def get_activity_external_references(self, username):
    #     a = self.get_athlete(username)
    #     if a is not None:
    #         for c in db.get_model_db():
    #             # activity = c.query(models.Activity)
    #             return c.query(models.Activity.external_reference).filter(models.Activity.athlete_id == a.id).load_only()
    #     return None

    # Core data only
    # def get_activity_core_data(self, username, start):

    #     start_date = self.get_start_date(start)

    #     athlete = self.get_athlete(username)

    #     data = []

    #     if athlete is not None:
    #         with sqlite3.connect(self.db_filename) as conn:
    #             cursor = conn.cursor()
    #             cursor.execute("select time, id, name, load, load_heartrate, intensity, ftp, lthr from activity where athlete_id = {}\
    #                  and activity.time >= datetime('{}') order by time desc".format(athlete.id, start_date.strftime("%Y-%m-%d")))
    #             for row in cursor.fetchall():
    #                 entry_time, id, name, load, load_heartrate, intensity, ftp, lthr = row
    #                 data.append((datetime.strptime(entry_time, '%Y-%m-%d %H:%M:%S'), id, name, int(load), int(load_heartrate), int(intensity), int(ftp), int(lthr)))
    #     return data

    # def get_activity_max_id(self, username):
    
    #     a = self.get_athlete(username)

    #     if a is not None:
    #         for c in db.get_model_db():
    #             return c.query(func.max(models.Activity.id)).filter(models.Activity.athlete_id == a.id).scalar()
        
    #     return -1



    # def get_single_zone_summary(self, username, zone, days_back_min, days_back_max):
    #     athlete = self.get_athlete(username)

    #     start_date = self.get_date_back(days_back_max)
    #     end_date = self.get_date_back(days_back_min)

    #     ret = []
    #     if athlete is not None:
    #         with sqlite3.connect(self.db_filename) as conn:
    #             cursor = conn.cursor()
    #             q = "SELECT activity_power_zone.zone, sum(activity_power_zone.time) 'seconds' \
    #             FROM activity join activity_power_zone on activity_power_zone.activity_id = activity.id \
    #             where activity_power_zone.zone = '{}' and activity.athlete_id = {} and activity.time > datetime('{}') and activity.time <= datetime('{}') \
    #             group by activity_power_zone.zone".format(zone, athlete.id, start_date.strftime("%Y-%m-%d %H:%M:%S"), end_date.strftime("%Y-%m-%d %H:%M:%S"))
    #             cursor.execute(q)
    #             for row in cursor.fetchall():
    #                 zone, seconds = row
    #                 ret.append((zone,seconds))
    #     return ret

    # Local Report Cache (Filesystem)

    # def get_pmc_data(self, username):
    #     athlete = self.get_athlete(username)
    #     df = pd.read_csv(service_report.filename_pmc_24months(config.get().get_file_cache_folder(), athlete.datakey))
    #     return df


