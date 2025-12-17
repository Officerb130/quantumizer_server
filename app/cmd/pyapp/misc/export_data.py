
import os
import time
import uuid
import shutil
import errno
import subprocess
import logging
# import loghelper
import csv
import re
import pypyodbc as pyodbc
import datetime
#import pyodbc

LOGGING_ID = 'script.contentwriter'
LOGGER = logging.getLogger(LOGGING_ID)


#################################
# Processing

import pandas as pd

def exportTransactions():

        _databasename = 'quantumizer'
        _strMachine = 'amos'
        _strLogin = 'quantum_user'
        _strPassword = 'budget'

        directory = "C:\\devel\\projects\\quantumizer\\data\\records\\alderson"

        constr = "Driver={SQL Server};Server=%s;Database=%s;uid=%s;pwd=%s" % (_strMachine, _databasename, _strLogin, _strPassword)
        
        con = pyodbc.connect(constr)
   
        c = con.cursor()

        # dt = datetime.datetime.strptime(row[0], '%d/%m/%Y').strftime('%m-%d-%Y')
        # desc = row[2].replace("'", "")
        strSQL = "select TransDate, t1.Description, Amount, s1.Description 'Source', s1.SourceType 'SourceType' \
             from quantumizer..TRANSACTION_LOG t1 join quantumizer..SOURCE s1 on t1.sourceid = s1.sourceid"

        dMonths = {}

        try:
            c.execute(strSQL)
            for row in c.fetchall():
                tdate, description,  amount, source, source_type = row

                dt = datetime.datetime.strptime(tdate, '%Y-%m-%d').strftime('%Y-%m')

                key = source + "_" + dt

                #print(key)

                data = dMonths.get(key, [])

                data.append({ 'transdate' : tdate, 'description' : description, 'amount' : amount, 'source' : source, 'source_type' : source_type})

                dMonths[key] = data

               # print("{} ,{}, {}, {}, {}".format(tdate, description, amount, source, source_type))
        except Exception as e:
                print("Error: {}".format(strSQL))

        for k in dMonths.keys():

            df = pd.DataFrame(dMonths[k])

            file = '{}/{}.h5'.format(directory, k)

            print("Output File: " + file)

            df.to_hdf(file, key='a', mode='w')

def exportClass():
    
        _databasename = 'quantumizer'
        _strMachine = 'amos'
        _strLogin = 'quantum_user'
        _strPassword = 'budget'

        directory = "C:\\devel\\projects\\quantumizer\\data\\records\\alderson"

        constr = "Driver={SQL Server};Server=%s;Database=%s;uid=%s;pwd=%s" % (_strMachine, _databasename, _strLogin, _strPassword)
        
        con = pyodbc.connect(constr)
   
        c = con.cursor()

        strSQL = "select s3.Description 'd1', s1.Description 'd2', t1.Pattern \
            from quantumizer..TRANSACTION_CLASS_DEFINITIONS t1 \
            join quantumizer..TRANSACTION_CLASS s1 on t1.classid = s1.classid \
            join quantumizer..TRANSACTION_CLASS_TO_GROUP s2 on s2.classid = s1.classid \
            join quantumizer..TRANSACTION_GROUP s3 on s3.groupid = s2.groupid"
   
        g = {}
        p = {}

        try:
            c.execute(strSQL)
            for row in c.fetchall():
                groupname, classname, pattern = row

        #         {"name": "Food", "hidden" : false, "group" : "Group1",
        # "classifiers": [ { "regex": ".*SAFEWAY.*" }, { "regex": ".*COLES.*" } ] }

                str = g.get(classname, "")
                patt = p.get(classname, "")

                if len(str) == 0:
                    str = "{{ \"name\": \"{}\", \"hidden\" : false, \"group\" : \"{}\", \"classifiers\": [".format(classname, groupname)

                if len(pattern) > 0:
                    pattern = pattern.replace("%", ".*")
                    if len(patt) > 0:
                        patt += ","
                    patt += "{{ \"regex\" : \"{}\" }} ".format(pattern)

                g[classname] = str
                p[classname] = patt

            for key in g.keys():
                str = g.get(key, "")
                patt = p.get(key, "")

                print(str + patt + "] },")




                # if groupname not in g:
                #     print("{{ \"name\" : \"{}\", \"hidden\" : false }},".format(groupname))

                # g.add(groupname)

                #print("{ \"name\" : \"{}\", \"hidden\" : false }".format(groupname))

                #print(key)

               # print("{} ,{}, {}, {}, {}".format(tdate, description, amount, source, source_type))
        except Exception as e:
                print("Error: {}".format(e))


if __name__ == '__main__':

    # logfilename = loghelper.LogHelper.getDateFileName('.\\log\\BudgetScanner','.log')
    # level = logging.DEBUG

    # lh = loghelper.LogHelper(lstLoggers = [LOGGING_ID], logLevel=level, filename=logfilename)

    #exportTransactions()

    exportClass()

    #exportGroup()
    
    #processDirectory(DEFINE_INPUT_DIRECTORY, DEFINE_BACKUP_DIRECTORY)

    
             




