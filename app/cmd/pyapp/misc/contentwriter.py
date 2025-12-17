import os
import time
import uuid
import shutil
import errno
import subprocess
import logging
import loghelper
import csv
import re
import pypyodbc as pyodbc
import datetime
#import pyodbc

LOGGING_ID = 'script.contentwriter'
LOGGER = logging.getLogger(LOGGING_ID)

DEFINE_INPUT_DIRECTORY = '.\\Quantumizer Input'
DEFINE_BACKUP_DIRECTORY = '.\\Backup'

#################################
# Processing

lstExtensions = [ '.csv' ]

def removeFile(file):
    if os.path.isfile(file):
        os.remove(file)
        return True
    return False

def moveFile(file, fileto):
    removeFile(fileto)
    if os.path.isfile(file):
        os.rename(file, fileto)
        return True
    return False

def processDirectory(strInDir, strBackupDir):

    count = 0

    for root, dirs, files in os.walk(strInDir):
        for f in files:
            if f[0] != '~':
                fullFile = root + '\\' + f
                fileName, fileExtension = os.path.splitext(f)
                if fileExtension in lstExtensions:
                    sourceID = fileName
                    pos = sourceID.find('_')
                    if pos > 0:
                        sourceID = sourceID[:pos]
                    bRet = processFile(sourceID, fullFile)
                    LOGGER.info("Conversion Result for '{}' = {}".format(f, "SUCCESS" if bRet == True else "FAIL"))
                    moveFile(fullFile, strBackupDir + '\\' + f)
                    count += 1

    LOGGER.info("Processed {} files".format(count))

def processFile(sourceID, inFile):

    lstRows = []

    with open(inFile, newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='"')
        for row in reader:
            if len(row) >= 3:
                lstRows.append(row)

    insertDB(sourceID, lstRows)

    LOGGER.info("Source: {} [Processed {} transactions]".format(sourceID, len(lstRows)))

    return True

def insertDB(source, rows):

        _databasename = 'quantumizer'
        _strMachine = '127.0.0.1'
        _strLogin = 'quantum_user'
        _strPassword = 'budget'

        constr = "Driver={SQL Server};Server=%s;Database=%s;uid=%s;pwd=%s" % (_strMachine, _databasename, _strLogin, _strPassword)
        
        con = pyodbc.connect(constr)
   
        c = con.cursor()

        for row in rows:
            dt = datetime.datetime.strptime(row[0], '%d/%m/%Y').strftime('%m-%d-%Y')
            desc = row[2].replace("'", "")
            strSQL = "EXEC TRANSACTION_INSERT '{}', '{}', '{}', {}".format(source, dt, desc, row[1])
            try:
                c.execute(strSQL)
                c.commit()
            except Exception as e:
                 LOGGER.info("Error: {}".format(strSQL))



if __name__ == '__main__':

    logfilename = loghelper.LogHelper.getDateFileName('.\\log\\BudgetScanner','.log')
    level = logging.DEBUG

    lh = loghelper.LogHelper(lstLoggers = [LOGGING_ID], logLevel=level, filename=logfilename)

    processDirectory(DEFINE_INPUT_DIRECTORY, DEFINE_BACKUP_DIRECTORY)

    
             




