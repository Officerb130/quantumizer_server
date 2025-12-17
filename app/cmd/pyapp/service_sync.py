import logging
import os
import json
import time
import glob
import sys
from .util import config
from . import db
import datetime
from datetime import timedelta
from . import service_base
import pandas as pd
import ntpath
import hashlib
import csv
import math
import random
import shutil

import warnings
warnings.filterwarnings('ignore',category=pd.io.pytables.PerformanceWarning)

LOGGING_ID = "SyncService"
LOGGER = logging.getLogger(LOGGING_ID)

###################################################
# Service

def makeDir(dir):
    try:
        os.stat(dir)
    except:
        os.mkdir(dir)

def getFileDetails(file):

    file = os.path.basename(os.path.normpath(file))

    pos = file.find("_")
    source = file[:pos]
    

    date = file[pos+1:]
    pos = date.find(".")
    if pos != -1:
        date = date[:pos]

    return source, date, "file"

def roundFloat(d):
    if d:
        return round(float(d),2)
    return None

class SyncService(service_base.BaseService):
    def __init__(self, daemon = False):
        super().__init__(name = LOGGING_ID, interval = config.get().SLEEP_INTERVAL, logger = LOGGER, cfg = config.get(), daemon=daemon)

    def check(self):
        self.checkInputFileSystem()
        self.checkFileSystem()

    def checkInputFileSystem(self):
    
        if config.get().ENABLE_SYNC_SERVICE != config.TRUE:
            return

        dir = self.cfg.DATA_FOLDER + "/input"

        clients = db.get().get_clients()

        for c in clients:

            data_dir = dir + "/" + c.name
            makeDir(data_dir)

            for folder in glob.glob(data_dir + "/*/"): 

                source = os.path.basename(os.path.normpath(folder))

                completed_dir = folder + "/completed"
                makeDir(completed_dir)

                dMonths = {}
                keyBackup = random.randint(1,1000)
                setFilenames = set()
     
                for filename in glob.glob(folder + "/*.csv", recursive = False): 

                    with open(filename, newline='') as csvfile:
                        reader = csv.reader(csvfile, delimiter=',', quotechar='"')
                        for row in reader:
                            if len(row) >= 3:
                                tdate, amount, description = row[0], row[1], row[2]
                                dt = datetime.datetime.strptime(tdate, '%d/%m/%Y').strftime('%Y-%m')
                                key = source + "_" + dt
                                v = dMonths.get(key, [])
                                data = []
                                if len(v) > 0:
                                    data = v[0]
                                date_db = datetime.datetime.strptime(tdate, '%d/%m/%Y').strftime('%Y-%m-%d')
                                data.append({ 'transdate' : date_db, 'description' : description.replace("'", ""), 'amount' : roundFloat(amount), 'source' : source, 'source_type' : 0 })
                                dMonths[key] = [data, filename]
                                setFilenames.add(filename)
                            # else:
                            #     print("skip")

                existingFiles = self.getClientFiles(c.name)

                for tMonth in dMonths.keys():
                    sourceNew, dateNew, source_typeNew = getFileDetails(tMonth)
                    fileStorage = '{}/{}.h5'.format(self.getClientFolder(c.name), tMonth)
    
                    df_orig = None
                    v = dMonths[tMonth]
                    addRows = v[0]
                    inputFilename = v[1]
                    skipped = 0

                    # Augment existing files
                    for efile in existingFiles:
                        source, date, source_type = getFileDetails(efile)
                        if source == sourceNew and date == dateNew:
                            df_orig = pd.read_hdf(efile)
                            addRows = []
                            inputRows = v[0]
                            for row in inputRows:
                                bSkip = False
                                for i in range(0, len(df_orig)):
                                    row_date = row['transdate']
                                    row_desc = row['description']
                                    row_amount = roundFloat(row['amount'])
                                    # Abort all
                                    if row_date is None or row_desc is None or row_amount is None:
                                        raise Exception("Input Row Error: {}".format(row))
                                    if df_orig.iloc[i]['transdate'] == row_date and df_orig.iloc[i]['description'] == row_desc \
                                        and roundFloat(df_orig.iloc[i]['amount']) == row_amount:
                                        bSkip = True
                                        skipped += 1
                                        break
                                if bSkip == False:
                                    addRows.append(row)

                    if len(addRows) > 0:
                        df_new = pd.DataFrame(addRows)

                        df = df_new

                        # Concat
                        if df_orig is not None:
                            df =  pd.concat([df_orig, df_new])                            
                            df_backup = completed_dir + "/{}_original_{}.csv".format(keyBackup, tMonth)
                            df_orig.to_csv(df_backup)

                        df = df.sort_values(by=['transdate'])

                        # df_orig.to_csv(tMonth + "_original.csv")
                        # df_new.to_csv(tMonth + "_add.csv")
                        # df.to_csv(tMonth + "_complete.csv")
                        # columns = ['transdate']
                        # df.loc[:,columns] = df[columns].applymap(str)

                        # overwrite existing
                        df.to_hdf(fileStorage, key='a', mode='w')

                        LOGGER.info("Source UPDATE: {}, Date: {} [Skipped {}, Added {} Records] to {} from {}".format(sourceNew, dateNew, skipped, len(addRows), fileStorage, inputFilename))

                for filename in setFilenames:
                    backupFilename = completed_dir + "/{}_import.csv".format(keyBackup)
                    shutil.copyfile(filename, backupFilename)
                    os.remove(filename)


    def getClientFolder(self, client):
        return self.cfg.CLIENT_FOLDER + "/" + client

    def getClientFiles(self, client):
    
        files = []
        data_dir = self.getClientFolder(client)
        for filename in glob.glob(data_dir + "/**/*.h5", recursive = True): 
            files.append(filename)
    
        return files

    def checkFileSystem(self):

        if config.get().ENABLE_SYNC_SERVICE != config.TRUE:
            return

        dir = self.cfg.CLIENT_FOLDER

        clients = db.get().get_clients()

        for c in clients:

            data_dir = dir + "/" + c.name

            try:
                os.stat(data_dir)
            except:
                os.mkdir(data_dir)

            skipfile = 0
            file_count = 0

            min_date = None

            for filename in glob.glob(data_dir + "/**/*.h5", recursive = True): 

                file = ntpath.basename(filename)

                file_count += 1

                source_hash = hashlib.md5(open(filename,'rb').read()).hexdigest()
                source_file = db.get().get_transaction_file_source(file, c.name)

                if source_file and source_hash == source_file.data_hash:
                    LOGGER.debug("Skip file '{}' -> hash unchanged".format(file))
                    skipfile += 1
                    continue

                df = pd.read_hdf(filename)

                source, date, source_type = getFileDetails(file)

                skipped = 0
                count = 0

                for index, row in df.iterrows():
                    if db.get().insert_transaction(row['transdate'], row['description'], row['amount'], source, source_type, c.name):

                        date_db = datetime.datetime.strptime(row['transdate'], '%Y-%m-%d')
                        if min_date is None or date_db < min_date:
                            min_date = date_db

                        count += 1
                    else:
                        skipped += 1
                    #print(row['dec'], row['id'])

                db.get().insert_update_transaction_source_file(file, c.name, source_hash)

                LOGGER.info("Added transactions [ Inserted: {}, Skipped: {}, Date: {}, Source: {}, Client: {} ]".format(count, skipped, date, source, c.name))

            if min_date:
                db.get().classify_transaction(min_date + timedelta(days=-1))

            if file_count-skipfile > 0:
                LOGGER.info("Added transactions [ Processed Files: {}, Skipped: {} ]".format(file_count-skipfile, skipfile))



