import os
import logging
import json
from .util import config

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQL_DB_FILE = "{}/cache/local.db".format(config.get().DATA_FOLDER)
SQLALCHEMY_DATABASE_URL = "sqlite:///" + SQL_DB_FILE

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

DB_MODE_SQLITE = "SQLITE"

LOGGING_ID = "Database"
LOGGER = logging.getLogger(LOGGING_ID)

from sqlalchemy.ext.declarative import DeclarativeMeta

class AlchemyEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj.__class__, DeclarativeMeta):
            # an SQLAlchemy class
            fields = {}
            for field in [x for x in dir(obj) if not x.startswith('_') and x != 'metadata']:
                data = obj.__getattribute__(field)
                try:
                    json.dumps(data) # this will fail on non-encodable values, like other classes
                    fields[field] = data
                except TypeError:
                    fields[field] = None
            # a json-encodable dict
            return fields

        return json.JSONEncoder.default(self, obj)

###################################################
# Database Interface

class DatabaseBase(object):
    def get_workouts(self):
        return None

    def get_row_count(self, table, filter = None):
        return 0

    # def sync_workouts_to_db(self):
    
    #     LOGGER.debug("Scanning workout folder: " + config.get().ZWO_FOLDER)

    #     zwo_files = zwohelper.load_zwo_files(config.get().ZWO_FOLDER, delay_init=True)

    #     folder_filename_md5 = {}
    #     for f in zwo_files:
    #         folder_filename_md5[f.get_filename()] = f.get_filename_md5()

    #     remove_count = 0 
    #     update_count = 0
    #     add_count = 0 

    #     db_filename_md5 = self.get_workout_source_from_db()
    #     zwo_files_delete = []
        
    #     # Workout in db, but no file
    #     for filename in db_filename_md5.keys():
    #         if filename not in folder_filename_md5.keys():
    #             zwo_files_delete.append(filename)
    #             remove_count += 1

    #     # Remove/Add changed
    #     # Add new
    #     zwo_files_add = []
        
    #     for f in zwo_files:
    #         md5 = db_filename_md5.get(f.get_filename(), None) 
    #         if md5 is None:
    #             zwo_files_add.append(f)
    #             add_count += 1
    #         elif md5 != f.get_filename_md5():
    #             zwo_files_delete.append(f.get_filename())
    #             zwo_files_add.append(f)
    #             update_count += 1

    #     # Release the memory
    #     zwo_files = None

    #     # Clear old/updatable records
    #     while len(zwo_files_delete) > 0:
    #         z = zwo_files_delete.pop()
    #         self.delete_workout(z)

    #     try:
    #         os.stat(config.get().IMAGE_FOLDER)
    #     except:
    #         os.mkdir(config.get().IMAGE_FOLDER)

    #     # Add
    #     while len(zwo_files_add) > 0:
    #         z = zwo_files_add.pop()
    #         LOGGER.info("Insert workout: {} ".format(z.get_filename()))
    #         z.init()
    #         id = self.insert_workout(z)
    #         if id >= 0:
    #             # CSV
    #             filename = zwohelper.ZWOHelper.filename_workout(config.get().get_file_cache_folder(), id)
    #             z.save_to_csv(filename)

    #         # Image for reference
    #         # filename = '{}/wo-{}.png'.format(config.get().IMAGE_FOLDER, z.get_name())
    #         # z.plot_to_file(filename)

    #     db_records = self.get_row_count('workout')

    #     info = "Workouts: {} (Added {}, Updated {}, Removed {})".format(db_records, add_count, update_count, remove_count)

    #     if (add_count + update_count + remove_count) > 0:
    #         LOGGER.info(info)
    #     else:
    #         LOGGER.debug(info)
