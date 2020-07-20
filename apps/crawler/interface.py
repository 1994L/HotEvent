from translate import Translator

from apps.crawler.crawl_news import NewsCrawler
from utils.aminer import Aminer
from utils.string_helper import contain_zh
from utils.logger import logRecord
from apps import cache

tlz = Translator('zh', 'en')


def getCrawlCondition(person: dict) -> tuple:
    '''
    获取抓取专家的基本信息作为抓取条件
    :param person:
    :return:
    '''
    name = person.get('name_zh') or person.get('name')
    profile = person.get('profile')
    org = None
    tags = person.get('tags')
    tag = None
    if tags:
        tag = tags[0]
    academic_type = None
    if profile:
        academic_type = profile.get('academic_type')
        if contain_zh(name):
            org = profile.get('affiliation_zh') or profile.get('affiliation', '')
            if org and not contain_zh(org):
                org = tlz.translate(org)
        else:
            org = profile.get('affiliation') or profile.get('affiliation_zh', '')
    return name, org, tag, academic_type, ''


def crawlNoKeywordNews(name: str, conditions: list) -> list:
    '''
    利用专家姓名+[org，tag，academic_type] 抓取，抓到新闻信息就退出
    :param name:
    :param conditions:
    :return:
    '''
    nc = NewsCrawler()
    for c in conditions:
        if c is not None:
            ret = nc.experts_news(name, c)
            if ret:
                logRecord(f'Search condition: {name}  {c}')
                return ret

@cache.memoize(timeout=60 * 20)
def crawlExpertsNews(ids: list, kw: str = None):
    '''
    抓取专家新闻主程序
    :param ids: 专家id列表
    :param kw: 抓取关键词
    :return:
    '''
    nc = NewsCrawler()
    items = Aminer.get_person_with_id(ids, profile_detail=False)
    if kw:
        experts = [{'name': person.get('name_zh') or person.get('name'), 'id': person['id']}
                   for person in items if person.get('name_zh') or person.get('name')]
        ret = nc.multi_crawl(experts, kw)
        return ret
    else:
        ret = []
        for item in items:
            conditions = getCrawlCondition(item)
            if conditions[0]:
                result = crawlNoKeywordNews(conditions[0], conditions[1:])
                ret.append({'id': item['id'], 'news': result})
        return ret

@cache.memoize(timeout=60 * 20)
def crawlExpertsEnNews(ids: list, kw: str = None):
    '''
    抓取专家新闻主程序
    :param ids: 专家id列表
    :param kw: 抓取关键词
    :return:
    '''
    nc = NewsCrawler('bing')
    items = Aminer.get_person_with_id(ids, profile_detail=False)
    if kw:
        experts = [{'name': person.get('name'), 'id': person['id']}
                   for person in items if person.get('name')]
        ret = nc.multi_crawl(experts, kw)
        return ret