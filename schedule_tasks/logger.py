import logging
import os

log_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')


def modify_logger(log_file):
    # refer: https://docs.python.org/3.5/library/logging.html#logrecord-attributes
    logger = logging.getLogger('scheduler')
    formatter = logging.Formatter(
        fmt='\n'.join([
            '[%(name)s] %(asctime)s.%(msecs)d',
            '\t%(pathname)s [line: %(lineno)d]',
            '\t%(processName)s[%(process)d] => %(threadName)s[%(thread)d] => %(module)s.%(filename)s:%(funcName)s()',
            '\t%(levelname)s: %(message)s\n'
        ]),
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    # stream_handler = logging.StreamHandler()
    # stream_handler.setFormatter(formatter)
    # logger.addHandler(stream_handler)
    file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.setLevel(logging.DEBUG)
    return logger


logger = modify_logger(log_path + '/scheduler.log')
