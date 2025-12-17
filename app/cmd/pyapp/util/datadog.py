import logging
import os
import configparser 
import json
import time
import sys
import requests
from . import config

import urllib3
urllib3.disable_warnings()

###################################################
# Datadog

import datadog

DD_METRIC_RATE = 'RATE'
DD_METRIC_GAUGE = 'GAUGE'

_dd_cache = None

class DDCache():

    def __init__(self):
        key = config.get().DD_API_KEY
        if key is not None and len(key) > 0:
            options = {'api_key': key }
            datadog.initialize(**options)

    def is_enabled(self):
        return config.get().DD_API_KEY is not None and len(config.get().DD_API_KEY) > 0

    def send_ddevent(self, text, a_type = 'info'):
        if self.is_enabled():
            tags = ['version_hash:' + config.get().getVersion(), 'source:' + config.get().SERVICE_NAME]
            return datadog.api.Event.create(title=config.get().SERVICE_NAME, text=text, tags=tags, alert_type=a_type)
        return None

    def send_ddmetric(self, name, points, tags = None, host = None, m_type=DD_METRIC_GAUGE):
        if tags is None:
            tags = []
        if self.is_enabled():
            tags.append('source:' + config.get().SERVICE_NAME)
            if host is not None:
                return datadog.api.Metric.send(
                    metric=name,
                    points=points,
                    tags=tags,
                    host=host,
                    type=m_type
                )
            else:
                return datadog.api.Metric.send(
                    metric=name,
                    points=points,
                    tags=tags,
                    type=m_type
                )
        return None

    # This goes to the local agent
    def send_ddtrace(self, trace, logger):
        if self.is_enabled():
            headers = {"Content-Type": "application/json", "X-Datadog-Trace-Count": "{}".format(len(trace))} 
            try:
                api = config.get().DD_TRACE_API
                logger.debug("Sent trace to " + api)
                requests.put(api, data=json.dumps(trace), headers=headers)
            except Exception as ex:
                logger.error("Failed to send trace -> " + str(ex))


def get() -> DDCache:
    global _dd_cache
    if not _dd_cache:
        _dd_cache = DDCache()
    return _dd_cache

def test_dd():
    l = logging.INFO

    logging.basicConfig(level=l, format='%(asctime)s %(name)s:[%(levelname)s]: %(message)s', datefmt='%Y-%m-%d %H:%M:%S') #NOSONAR
    get().send_ddmetric('service.imc.health.gauge', 2, ['appname:IOSPLUSTE', 'instance:IOS_TEST'], 'MY_HOST')

if __name__ == '__main__':
    test_dd() 