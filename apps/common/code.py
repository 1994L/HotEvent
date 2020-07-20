

class Code:
    OK = 0
    DB_ERROR = 4001
    PARAM_ERROR = 4101
    UNKNOWN_ERROR = 4201
    CUSTOM_ERROR = 4301
    msg = {
        0: 'success',
        4001: 'db error',
        4101: 'param error',
        4201: 'failed'
    }
