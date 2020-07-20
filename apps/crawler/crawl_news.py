import requests
import re
import time
import random
from datetime import datetime, timedelta
from lxml import etree
from concurrent.futures import ThreadPoolExecutor, wait, ALL_COMPLETED
from urllib.parse import quote_plus

from utils.decorators import timing
from utils.string_helper import contain_en, remove_symbol, contain_zh
from utils.logger import logRecord


USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36",
    "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Win64; x64; Trident/5.0; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET CLR 2.0.50727; Media Center PC 6.0)",
    "Mozilla/5.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET CLR 1.0.3705; .NET CLR 1.1.4322)",
    "Mozilla/4.0 (compatible; MSIE 7.0b; Windows NT 5.2; .NET CLR 1.1.4322; .NET CLR 2.0.50727; InfoPath.2; .NET CLR 3.0.04506.30)",
    "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN) AppleWebKit/523.15 (KHTML, like Gecko, Safari/419.3) Arora/0.3 (Change: 287 c9dfb30)",
    "Mozilla/5.0 (X11; U; Linux; en-US) AppleWebKit/527+ (KHTML, like Gecko, Safari/419.3) Arora/0.6",
    "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.1.2pre) Gecko/20070215 K-Ninja/2.1.1",
    "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN; rv:1.9) Gecko/20080705 Firefox/3.0 Kapiko/3.0",
    "Mozilla/5.0 (X11; Linux i686; U;) Gecko/20070322 Kazehakase/0.4.5"
    "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; AcooBrowser; .NET CLR 1.1.4322; .NET CLR 2.0.50727)",
    "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; Acoo Browser; SLCC1; .NET CLR 2.0.50727; Media Center PC 5.0; .NET CLR 3.0.04506)",
    "Mozilla/4.0 (compatible; MSIE 7.0; AOL 9.5; AOLBuild 4337.35; Windows NT 5.1; .NET CLR 1.1.4322; .NET CLR 2.0.50727)",
    "Mozilla/5.0 (Windows; U; MSIE 9.0; Windows NT 9.0; en-US)",
    "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.8) Gecko Fedora/1.9.0.8-1.fc10 Kazehakase/0.5.6",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.56 Safari/535.11",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_3) AppleWebKit/535.20 (KHTML, like Gecko) Chrome/19.0.1036.7 Safari/535.20",
    "Opera/9.80 (Macintosh; Intel Mac OS X 10.6.8; U; fr) Presto/2.9.168 Version/11.52",
]


def get_ua():
    return random.choice(USER_AGENTS)


class NewsCrawler:
    SOURCES = {
        'baidu':'http://www.baidu.com/s?ie=utf-8&cl=2&medium=1&rtt=4&bsst=1&rsv_dl=news_t_sk&tn=news&word={}',
        'bing': 'https://cn.bing.com/search?q={}&itype=web&FORM=BESBTB&ensearch=1&iname=bing&isource=infinity'
    }
    HEADERS = {
        'baidu': {
            'Connection': 'keep-alive',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': get_ua(),
            # 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-Mode': 'navigate',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
        },
        'bing': {
            'user-agent': get_ua(),
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'accept-language': 'zh-CN,zh;q=0.9',
            'cookie': f'SRCHHPGUSR=HV={int(time.time())}'
        }
    }
    def __init__(self, source='baidu'):
        self.source = source
        self.result = []


    def request_html(self, query):
        '''
        请求html页面
        :param query:
        :return:
        '''
        url = self.SOURCES.get(self.source)
        headers = self.HEADERS.get(self.source)
        assert url
        count = 0
        while count < 5:
            try:
                resp = requests.get(url.format(query), headers=headers, timeout=2)
                break
            except:
                logRecord(f'{self.source} request timeout!', 'error')
                time.sleep(1)
                count += 1
        else:
            return None
        if resp.status_code == 200:
            return resp.text
        else:
            logRecord(f'ERROR! {resp.status_code}!', 'error')
            return None

    def baidu_query(self, query):
        return ' '.join(query)

    def bing_query(self, query):
        if len(query) == 1:
            return query[0]
        elif len(query) == 2:
            return f'{query[0]} "{query[1]}"'
        else:
            return ' '.join(query)

    def baidu_parse(self, text, query=None):
        '''
        解析百度html
        :param text:
        :param query:
        :return:
        '''
        ret = []
        text = text.replace('<em>', '').replace('</em>', '')
        html = etree.HTML(text)
        results = html.xpath('//div[@id="content_left"]//div[@class="result"]')
        for rs in results:
            title = ''.join(rs.xpath('h3/a//text()')).replace('\n', ' ').strip()
            news_url = rs.xpath('h3/a/@href')
            news_source, news_time = [i.strip() for i in ''.join(rs.xpath(
                'div//p[@class="c-author"]/text()')).replace('\n', '').replace('\t', '').split('\xa0\xa0')]
            news_time_sub = None
            if '分钟' in news_time:
                news_time_stamp = news_time.split('分钟')[0]
                news_time_sub = int(news_time_stamp) * 60
            elif '小时' in news_time:
                news_time_stamp = news_time.split('小时')[0]
                news_time_sub = int(news_time_stamp) * 60 * 60
            if news_time_sub:
                time_stamp = time.time() - news_time_sub
                news_time = time.strftime('%Y年%m月%d日 %H:%M', time.localtime(time_stamp))
            # print(news_source, news_time)
            desc_tag = rs.xpath('div/div[@class="c-span18 c-span-last"]')
            if not desc_tag:
                desc_tag = rs.xpath('div')
            desc = ''.join(desc_tag[0].xpath('text()')).replace('\n', ' ').strip()
            if query:
                field1, field2 = query
                text = title + desc
                if contain_zh(field1):
                    filter_query = field1 in text and field2 in text
                else:
                    filter_query = self.filter_news(field1, field2, text)
            else:
                filter_query = True
            if filter_query:
                ret.append({
                    'title': title,
                    'source': news_source,
                    'time': news_time,
                    'desc': desc,
                    'url': news_url[0] if news_url else ''
                })
        return ret

    def bing_parse(self, text, query=None):
        '''
        解析必应国际版html
        :param text:
        :param query:
        :return:
        '''
        # print(text)
        assert len(query) == 2
        name, keyword = query
        ret = []
        html = etree.HTML(text)
        results = html.xpath('//ol[@id="b_results"]/li[@class="b_algo"]')
        for li in results:
            title = ''.join(li.xpath('h2/a//text()'))
            news_url = li.xpath('h2/a/@href')
            desc = li.xpath('div[@class="b_caption"]/p//text()')
            desc = ''.join(desc).replace('\n', ' ').strip()
            time = desc.split('\xa0')[0]
            if 0 < len(time) <= 12:
                now = datetime.now()
                if 'day' in time:
                    delta_days = int(time.split('day')[0].strip())
                    news_time = now + timedelta(days=-delta_days)
                elif 'hour' in time:
                    delta_hours = int(time.split('hour')[0].strip())
                    news_time = now + timedelta(hours=-delta_hours)
                else:
                    news_time = datetime.strptime(time, '%b %d, %Y')
                time = news_time.strftime('%Y年%m月%d日')
            else:
                time = ''
            desc = desc.split('\xa0')[-1]
            if self.filter_news(name, keyword, title+desc):
                ret.append({
                    'title': title,
                    'time': time,
                    'desc': desc,
                    'url': news_url[0] if news_url else ''
                })
        ret = sorted(ret, key=lambda x: x['time'], reverse=True)
        return ret

    def crawl(self, *args):
        '''
        抓取专家新闻主程序
        :param args:
        :return:
        '''
        if len(args) == 2:
            query = getattr(self, f'{self.source}_query')(args)
            result_text = self.request_html(query)
            ret = getattr(self, f'{self.source}_parse')(result_text, args)
            return ret
        elif len(args) == 3:
            id = args[-1]
            result_text = self.request_html(args[:2])
            ret = getattr(self, f'{self.source}_parse')(result_text, args[:2])
            self.result.append({'id': id, 'news': ret})

    @timing
    def multi_crawl(self, experts: list, kw: str):
        '''
        多线程抓取专家新闻
        :param experts:
        :param kw:
        :return:
        '''
        pool_size = min(len(experts), 10)
        pool = ThreadPoolExecutor(pool_size)
        ret = []
        for ex in experts:
            ret.append(pool.submit(self.crawl, ex['name'], kw, ex['id']))
        wait(ret, return_when=ALL_COMPLETED)
        return self.result

    def filter_baidu_news(self, news, ems, args):
        '''
        中英文皆可
        :param news:
        :param ems:
        :param args:
        :return:
        '''
        ret = []
        if not contain_en(' '.join(args)):
            query_word = set([j for i in args for j in i])
            for i, item in enumerate(news):
                em = set([e for em in ems[i] for e in em])
                if len(query_word.difference(em)) == 0:
                    ret.append(item)
        else:
            query_word = set([i for i in remove_symbol(' '.join(args)).split(' ') if i])
            for i, item in enumerate(news):
                em = set([i for i in remove_symbol(' '.join(ems[i])).split(' ') if i])
                if len(em.intersection(query_word)) == len(query_word):
                    ret.append(item)
        return ret

    def filter_news(self, name: str, keyword: str, text: str) -> bool:
        '''
        只接受英文
        :param name:
        :param keyword:
        :param text:
        :return:
        '''
        name = name.lower()
        keyword = keyword.lower()
        text = text.lower()
        name_list = name.split()
        count = 0
        for n in name_list:
            if n in text:
                count += 1

        if count >= 2 and keyword in text:
            return True
        else:
            return False

    def experts_news(self, *args):
        '''
        当没有关键词的时候，依靠姓名、机构或者学者领域抓取专家新闻可能不准确，所以进行过滤筛选。
        :param args:
        :return:
        '''
        result_text = self.request_html(args)
        fields = self.baidu_parse(result_text)
        ems = self.baidu_parse_ems(result_text)
        ret = self.filter_baidu_news(fields, ems, args)
        return ret

    def baidu_parse_ems(self, text):
        '''
        获取baidu页面em标签：命中的搜索条件会用em标签
        :param text:
        :return:
        '''
        ret = []
        html = etree.HTML(text)
        results = html.xpath('//div[@id="content_left"]//div[@class="result"]')
        for rs in results:
            item = []
            emt = rs.xpath('h3//em/text()')
            emd = rs.xpath('div//em/text()')
            item.extend(emt)
            item.extend(emd)
            ret.append(item)
        return ret


if __name__ == '__main__':
    ret = NewsCrawler('bing').crawl('Stephen M. Schwartz', 'virus')
    for i in ret:
        print(i)











