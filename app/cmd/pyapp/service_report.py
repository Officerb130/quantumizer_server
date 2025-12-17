import logging
import os
import json
import time
import glob
import sys
from .util import config
from . import db
from . import service_base
from . import db_imp
import csv
import pandas as pd
from .util import taskrunner
from datetime import datetime, timedelta
import pendulum

LOGGING_ID = "ReportService"
LOGGER = logging.getLogger(LOGGING_ID)

###################################################
# Service

DT_POWER = "power"
DT_HEART_RATE = "heart_rate"
DT_LOAD = "load"

def filename_pmc_24months(folder, datakey):
    return "{}/{}_pmc_24months.csv".format(folder, datakey)

def filename_efficiency_24months(folder, datakey):
        return "{}/{}_efficiency_24months.csv".format(folder, datakey)

def filename_power_curve_24months(folder, datakey):
        return "{}/{}_power_curve_summary_24months.csv".format(folder, datakey)

def filename_zone_summary_3months(folder, datakey, dt):
    return "{}/{}_{}_zone_summary_3months.csv".format(folder, datakey, dt)

def filename_load_summary_3months(folder, datakey):
    return "{}/{}_load_summary_3months.csv".format(folder, datakey)


class ReportService(service_base.BaseService):
    def __init__(self, daemon = False):
        super().__init__(name = LOGGING_ID, interval = config.get().SLEEP_INTERVAL, logger = LOGGER, cfg = config.get(), daemon=daemon)
        self.athlete_max_id = {}

    def reset_athlete(self, id):
        self.athlete_max_id[id] = None

    def check(self):

        if config.get().ENABLE_REPORT_SERVICE != config.TRUE:
            return

        return
        
        dir = self.cfg.ATHLETE_FOLDER

        try:
            os.stat(self.cfg.get_file_cache_folder())
        except:
            os.mkdir(self.cfg.get_file_cache_folder())

        for d in glob.glob(dir + "/*/", recursive = False):

            athlete_name = os.path.basename(os.path.normpath(d))

            a = db.get().get_athlete(athlete_name)

            if a is None:
                LOGGER.error("Athlete db data not found '{}'...".format(athlete_name))
                continue

            # Don't regenerate if data is the same
            max_db = db.get().get_activity_max_id(athlete_name)
            current_max = self.athlete_max_id[athlete_name] if athlete_name in self.athlete_max_id.keys() else 0
            if max_db is None:
                max_db = 0
            if max_db <= current_max:
                LOGGER.debug("Skip '{}' -> no change in data".format(athlete_name))
                continue

            LOGGER.info("Creating summary data for athlete '{}'...".format(athlete_name))

            dt = taskrunner.DurationTimer()

            today = pendulum.now()
            start = today.start_of('week')
            dif = today - start 

            # Zone Summaries
            for r in [DT_POWER, DT_HEART_RATE]:
                file = filename_zone_summary_3months(self.cfg.get_file_cache_folder(), a.datakey, r)
                with open(file, 'w', newline='') as csvfile:
                    fieldnames = None
                    if r == DT_POWER:
                        fieldnames = ['group'] + fitness.get_power_zone_list()
                    elif r == DT_HEART_RATE:
                        fieldnames = ['group'] + fitness.get_hr_zone_list()
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    rows = []
                    start = 0
                    # Weekly
                    max = 13
                    # 12 Weeks
                    for i in range(1, max):
                        inc = 7
                        if i == 1:
                            inc = dif.days + 1
                        zone_data = get_consolidated_row(r, athlete_name, "W{}".format(max-i), start, start+inc)
                        rows.insert(0, zone_data)
                        start += inc
                    for r in rows:
                        writer.writerow(r)
                        
            # Load Summary
            file = filename_load_summary_3months(self.cfg.get_file_cache_folder(), a.datakey)
            with open(file, 'w', newline='') as csvfile:
                fnames = ['load', 'duration', 'distance', 'intensity']
                fieldnames = ['group', 'start', 'end'] + fnames
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                rows = []
                start = 0
                # Weekly
                max = 13
                # 12 Weeks
                for i in range(1, max):
                    inc = 7
                    if i == 1:
                        inc = dif.days + 1
                    zone_data = get_consolidated_row(DT_LOAD, athlete_name, "W{}".format(max-i), start, start+inc, field_names=fnames, addtime=True)
                    rows.insert(0, zone_data)
                    start += inc
                for r in rows:
                    writer.writerow(r)

            # 24 month power curve by month
            file = filename_power_curve_24months(self.cfg.get_file_cache_folder(), a.datakey)
            start = 0
            # Monthly
            inc = 30
            # 24 Months
            max = 24
            rows = []
            for i in range(0, max):
                data = db.get().get_activity_power_curve_max(athlete_name, start, start+inc)
                for e in data:
                    #e['group'] = "M{}".format(max-i)
                    e['group'] = "{}".format(i+1)
                    rows.append(e)
                start += inc
            df = pd.DataFrame(rows)
            df.to_csv(file)

            # 24 Month efficiency
            file = filename_efficiency_24months(self.cfg.get_file_cache_folder(), a.datakey)
            data = db.get().get_activity_efficiency(athlete_name, db_imp.Database.START_24MONTHS, [activity.ACTIVITY_TYPE_RIDE, activity.ACTIVITY_TYPE_RIDE_VIRTUAL], "All")
            df = pd.DataFrame(data)
            data = db.get().get_activity_efficiency(athlete_name, db_imp.Database.START_24MONTHS, [activity.ACTIVITY_TYPE_RIDE], activity.ACTIVITY_TYPE_RIDE)
            df_r = pd.DataFrame(data)
            data = db.get().get_activity_efficiency(athlete_name, db_imp.Database.START_24MONTHS, [activity.ACTIVITY_TYPE_RIDE_VIRTUAL], activity.ACTIVITY_TYPE_RIDE_VIRTUAL)
            df_rv = pd.DataFrame(data)
            df = df.merge(df_r, how='left', on='time')
            df = df.merge(df_rv, how='left', on='time')
            df.to_csv(file)

            # PMC Data
            data = db.get().get_activity_core_data(athlete_name, db_imp.Database.START_24MONTHS)
            if data:
                file = "{}/{}_activities_24months.csv".format(self.cfg.get_file_cache_folder(), a.datakey)
                with open(file, 'w', newline='') as csvfile:
                    fieldnames = ['date', 'id', 'name', 'load', 'load_heartrate', 'intensity', 'ftp', 'lthr']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    for r in data:
                        writer.writerow({'date': r[0], 'id' : r[1], 'name' : r[2], 'load': r[3], 'load_heartrate': r[4], 'intensity': r[5],
                        'ftp': r[6], 'lthr': r[7]})

                pmc_data = fitness.get_pmc_data(data)

                if pmc_data is not None:
                    file = filename_pmc_24months(self.cfg.get_file_cache_folder(), a.datakey)
                    pmc_data.to_csv(file, index=False)

            self.athlete_max_id[athlete_name] = max_db

            LOGGER.info("Summary data COMPLETE for athlete '{}' ({})".format(athlete_name, dt))


