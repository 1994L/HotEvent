import traceback

from apps import app


CRITICAL = 50
FATAL = CRITICAL
ERROR = 40
WARNING = 30
WARN = WARNING
INFO = 20
DEBUG = 10
NOTSET = 0

_levelToName = {
    CRITICAL: 'CRITICAL',
    ERROR: 'ERROR',
    WARNING: 'WARNING',
    INFO: 'INFO',
    DEBUG: 'DEBUG',
    NOTSET: 'NOTSET',
}
_nameToLevel = {
    'CRITICAL': CRITICAL,
    'FATAL': FATAL,
    'ERROR': ERROR,
    'WARN': WARNING,
    'WARNING': WARNING,
    'INFO': INFO,
    'DEBUG': DEBUG,
    'NOTSET': NOTSET,
}


def logRecord(msg, level='info', debug=None):
    levelNum = _nameToLevel.get(level.upper())
    if levelNum:
        if debug is None:
            detail = app.debug
        else:
            detail = debug
        if detail:
            errMsg = traceback.format_exc()
            if errMsg.strip() == 'NoneType: None':
                app.logger.log(levelNum, msg)
            else:
                app.logger.log(levelNum, errMsg)
        else:
            app.logger.log(levelNum, msg)


if __name__ == '__main__':
    try:
        raise Exception(132)
    except Exception as e:
        logRecord('123','error')
    print(666)

