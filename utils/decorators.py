import time
import signal
from time import ctime

from utils.logger import logRecord


class TimeoutError(Exception):
    def __init__(self, msg):
        super(TimeoutError, self).__init__()
        self.msg = msg


def time_out(interval):
    def decorator(func):
        def handler(signum, frame):
            raise TimeoutError("run func timeout")

        def wrapper(*args, **kwargs):
            try:
                signal.signal(signal.SIGALRM, handler)
                signal.alarm(interval)  # interval秒后向进程发送SIGALRM信号
                result = func(*args, **kwargs)
                signal.alarm(0)  # 函数在规定时间执行完后关闭alarm闹钟
                return result
            except TimeoutError as e:
                logRecord(e.msg, level='error')

        return wrapper

    return decorator


def timeout_callback(e):
    print(e.msg)


def timing(f):
    def inner(*args, **kwargs):
        time1 = time.time()
        ret = f(*args, **kwargs)
        time2 = time.time()
        logRecord('[{0}] {1}() called, time delta: {2}s'.format(ctime(), f.__name__, round(time2 - time1, 2)))
        return ret

    return inner
