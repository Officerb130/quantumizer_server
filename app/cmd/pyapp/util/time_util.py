from datetime import datetime, timedelta
import time

PERIOD_DAY=0
PERIOD_WEEK=1
PERIOD_MONTH=2

START_1MONTH="1 Month"
START_3MONTHS="3 Months"
START_6MONTHS="6 Months"
START_12MONTHS="12 Months"
START_24MONTHS="24 Months"
START_36MONTHS="36 Months"
START_48MONTHS="48 Months"
START_ALL="All"

YEAR_DAYS = 365

def get_start_date(start):

    if start == START_ALL:
        return None
    
    start_date = datetime.today()

    if start == START_1MONTH:
        start_date = datetime.today() #+ timedelta(days=-30)
    elif start == START_3MONTHS:
        start_date = datetime.today() + timedelta(days=-int(YEAR_DAYS/4))
    elif start == START_6MONTHS:
        start_date = datetime.today() + timedelta(days=-int(YEAR_DAYS/2))
    elif start == START_12MONTHS:
        start_date = datetime.today() + timedelta(days=-int(YEAR_DAYS))
    elif start == START_24MONTHS:
        start_date = datetime.today() + timedelta(days=-int(YEAR_DAYS*2))
    elif start == START_36MONTHS:
        start_date = datetime.today() + timedelta(days=-int(YEAR_DAYS*3))
    elif start == START_48MONTHS:
        start_date = datetime.today() + timedelta(days=-int(YEAR_DAYS*4))

    start_date = start_date.replace(day=1)
    start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)

    return start_date

def get_date_back(days):
    
    date = datetime.today() + timedelta(days=-days)
    date = date.replace(hour=23, minute=59, second=59, microsecond=0)

    return date

def get_period_format(period):
    
    group = '%Y-%m'

    if period == PERIOD_DAY:
        group = '%Y-%m-%d'
    elif period == PERIOD_MONTH:
        group = '%Y-%m'

    return group

class DurationTimer(object):
    
    def __init__(self):
        self.started = time.time()
        self.stopped = 0

    def start(self):
        self.started = time.time()
        self.stopped = 0
        return self

    def stop(self):
        if self.started > 0:
            self.stopped = time.time()
        return self

    def duration(self):
        if self.stopped == 0:
            self.stopped = time.time()
        return int(round((self.stopped - self.started) * 1000, 0))

    def __str__(self):
        # if self.started == 0:
        #     return 'not-running'
        # if self.started > 0 and self.stopped == 0:
        #     return 'started: %d (running)' % self.started
        return DurationTimer.formatTime(self.duration())

    @staticmethod
    # convert to a readable string
    def formatTime(durationMS):
        if durationMS < 1000:
            return '%d millisecond(s)' % durationMS
        if durationMS < 60 * 1000:
            return '%d second(s)' % int(durationMS / 1000)
        min = int(durationMS / (60 * 1000))
        sec = int((durationMS / (60 * 1000) - min) * 60)
        if sec == 0:
            return '{MIN} minute(s)'.format(MIN=min)
        return '{MIN} minute(s) {SEC} second(s)'.format(MIN=min, SEC=sec)