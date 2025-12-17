"""Central place to setup needed config

All config via environment variables for now
"""
import os

from pydantic import BaseSettings

_config_cache = None

TRUE = "TRUE"
FALSE = "FALSE"

class ServiceConfig(BaseSettings):

    SLEEP_INTERVAL: int = 60
    SERVICE_NAME: str = "QUANTUMIZER"
    DD_API_KEY: str = ""
    DD_TRACE_API: str = ""
    DATA_FOLDER: str = ""
    CLIENT_FOLDER: str = ""
    DB_MODE: str = ""
    ENABLE_SYNC_SERVICE: str = TRUE
    ENABLE_REPORT_SERVICE: str = TRUE
    IMAGE_FOLDER: str = "pyapp/static/images"
    RESULT_LIMIT: int = 20
    ACCESS_DB_SECRET: str = os.urandom(24).hex()
    ACCESS_TOKEN_EXPIRY_SECONDS: int =  24 * 60 * 60 * 14 # 14 Days
    DEFAULT_LOGIN_NAME: str =  ""

    PORT: str = "8199"

    def get_file_cache_folder(self):
        return self.DATA_FOLDER + "/file_cache"

    class Config:
        extra = 'allow'

def get(cfg = None) -> ServiceConfig:
    global _config_cache
    if not _config_cache:
        _config_cache = ServiceConfig.parse_obj(dict(os.environ))
        if cfg:
            _config_cache.load(cfg)
    return _config_cache