import os

ERROR_INTERNAL = 0
ERROR_AUTH = 1
ERROR_NOT_FOUND = 2
ERROR_INVALID_PARAMETERS = 4

ERRORS = {
    ERROR_INTERNAL : "Internal Failure",
    ERROR_AUTH : "Authentication Failure",
    ERROR_NOT_FOUND : "Not Found",
    ERROR_INVALID_PARAMETERS : "Invalid Parameters"
}

def get_error_json(error):
    return { "errorid" : error, "desc" : ERRORS[error] }

def get_error_json_str(error, desc):
    return { "errorid" : error, "desc" : desc }