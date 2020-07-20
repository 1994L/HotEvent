import datetime
from schedule_tasks import tasks
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from schedule_tasks.send_email import EmailTools

from schedule_tasks.logger import logger

sender_name = '苏平'
sender_url = 'ping.su@aminer.cn'
sender_pwd = 'cxsp.1119'
receiver_name = '预测组'
receiver_urls = ['su752143565@163.com', 'bing_lun1994@163.com', 'jizhong.du@aminer.cn']
smtp = 'smtp.mxhichina.com'


def ncov_task1():
    '''
    定时更新dxy全国全国数据
    :return:
    '''
    print(f'[{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}]  update_overall')
    logger.info(f'[{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}]  update_overall')
    tasks.update_overall_timed()


def ncov_task2():
    '''
    9:58分执行丁香园疫情数据抓取
    :return:
    '''
    print(f'[{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}]  crawl_dxy')
    logger.info(f'[{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}]  crawl_dxy')
    tasks.crawl_dxy()


def ncov_task3():
    '''
    23:58执行保存当天预测数据
    :return:
    '''
    print(f'[{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}]  save_predict_history')
    logger.info(f'[{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}]  save_predict_history')
    tasks.save_predict_history()


def my_listener(event):
    if event.exception:
        logger.info(event.job_id)
        logger.info(event.exception)
        em = EmailTools(sender_name, sender_url, sender_pwd, receiver_name, receiver_urls, smtp)
        em.send_email(f'{event.job_id}: \n{event.exception}', '定时任务错误')
    else:
        logger.info(f'{event.job_id}: 正常进行')
        if event.job_id == 'crawl_dxy' or event.job_id == 'save_predict':
            em = EmailTools(sender_name, sender_url, sender_pwd, receiver_name, receiver_urls, smtp)
            em.send_email(f'{event.job_id}: \n执行成功！！！', '定时任务成功')


def dojob():
    # 创建调度器：BlockingScheduler
    scheduler = BlockingScheduler()
    # 添加任务,时间间隔2S
    now = datetime.datetime.now()
    new_time = now.replace(hour=now.hour+1, minute=1)
    scheduler.add_job(ncov_task1, 'interval', minutes=60, id='update_overall', next_run_time=new_time)
    # 添加任务,时间间隔5S
    scheduler.add_job(ncov_task2, 'cron', hour=9, minute=58, id='crawl_dxy')
    scheduler.add_job(ncov_task3, 'cron', hour=18, minute=30, id='save_predict')

    # scheduler.add_listener(my_listener, EVENT_JOB_EXECUTED|EVENT_JOB_ERROR)
    # scheduler._logger = logging.getLogger('task')
    logger.info('scheduler start ')
    scheduler.start()


if __name__ == '__main__':
    dojob()