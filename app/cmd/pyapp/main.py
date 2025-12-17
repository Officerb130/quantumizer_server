import logging
import os
from .util import config
from .util import datadog
from . import service_sync
from . import service_report

import uvicorn
from . import db
import random
from .util import security
from .util import key_killer
from pathlib import Path
from . import api_webui

LOGGING_ID = "Main"
LOGGER = logging.getLogger(LOGGING_ID)

###################################################
# Main

def main():

    import argparse

    parser = argparse.ArgumentParser(description='Debug')
    parser.add_argument('-d', help='Debug trace', action="store_true")
    args = parser.parse_args()

    l = logging.INFO
    if args.d:
        l = logging.DEBUG

    logging.basicConfig(level=l,format='%(asctime)s %(name)s:[%(levelname)s]: %(message)s', datefmt='%Y-%m-%d %H:%M:%S') #NOSONAR

    datadog.get().send_ddevent(config.get().SERVICE_NAME + ' Started')

    key_killer.echo_input(False)

    # Init DB
    db.get()

    service_sync.SyncService(daemon=True).start()
    service_report.ReportService(daemon=True).start()

    # logging.getLogger('uvicorn.error').setLevel(logging.CRITICAL+1)
    # logging.getLogger('uvicorn.access').setLevel(logging.CRITICAL+1)

    # API
    app = api_webui.getApp()

    cfg = uvicorn.Config(
            app,
            host="0.0.0.0",
            port=int(config.get().PORT),
            lifespan="off",
            log_config = None)
            # workers=10)

    server = uvicorn.Server(config=cfg)

    server.run()

    key_killer.echo_input(True)
    key_killer.flush_input()


if __name__ == '__main__':
    main() 