import os
import threading
import sys
import logging

DEF_SLEEP_INTERVAL = 60
###################################################
# Service

class BaseService(threading.Thread):
    def __init__(self, name = "Default", interval = DEF_SLEEP_INTERVAL, logger = None, cfg = None, daemon = False):
        self.logger = logger
        super().__init__(daemon=daemon)
        self._kill = threading.Event()
        self.cfg = cfg
        self.name = name
        self._interval = interval

    def kill(self):
        self._kill.set()

    def run(self):
        self.logger.info("Start Service [Name = {}, Timer = {}sec]".format(self.name, self._interval))
        while True:
            self.__check()
            is_killed = self._kill.wait(self._interval)
            if is_killed:
                break
        self.logger.info("Stop Service [Name = {}]".format(self.name))

    def __check(self):
        try:
            self.check()
        except Exception as ex:
            self.logger.info("{} : Timer Event Failed -> {}".format(self.name, str(ex)))
            pass

    def check(self):
        pass


