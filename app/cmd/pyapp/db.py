import os
from . import db_base
from . import db_imp
from .util import config

###################################################
# Database Instance

# DB
db_base.Base.metadata.create_all(bind=db_base.engine)

_database_cache = None

def get() -> db_base.DatabaseBase:
    global _database_cache
    if not _database_cache:
        if config.get().DB_MODE == "":
            _database_cache = db_imp.Database()
    return _database_cache

def get_model_db():
    try:
        db = db_base.SessionLocal()
        yield db
    finally:
        db.close()

def get_model_engine():
    return db_base.engine
