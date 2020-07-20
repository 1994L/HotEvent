import requests as rq
import json
import multiprocessing
import traceback
from datetime import datetime

from utils.logger import logRecord
from utils.match_paper import match_aminer_paper
from utils.decorators import timing
from utils.string_helper import remove_symbol_nospace


class Aminer:
    headers = {
        'Connection': "keep-alive",
        'Accept': "application/json, text/plain, */*",
        'Origin': "https://www.aminer.cn",
        # please update token once a month
        'Authorization': "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIyLXF1cUk2Uno0akRCckFRODFzTG83UzVKazRRVlV0MFlpK2lENGpIdlZrMHcrSWhRSlVkM3Q4NXU4NVordEVWZFVIWUJEOWR3dDFHUmUwUFJnaDVUNWxTRmxuSGc2WnhUK0wrTkNETXFWSXc9PSIsInVpZCI6IjU2ZThmZGUyNzZkOTExNzRhNzM5YjQxNCIsInNyYyI6ImFtaW5lciIsInJvbGVzIjpbInJvb3QiXSwiaXNzIjoiYXBpLmFtaW5lci5vcmciLCJleHAiOjE1NTgxNjU5NjcsImlhdCI6MTU1NTU3Mzk2NywianRpIjoiMDE2NWRiNmY1MDU3MWNlNzUxODM1YjU3YjgyMWU3MzgwYjcwYjE0ODljZjA1MDg0NjM0ODRlMjNmZmY3OTVjY2Y4NzgyZTY1ZjI0MmM1ZTllNjAwMzViN2FmZTU5ZWUxNWQ0YmU1NWY2NmJmM2ZiMGE0ZDJkNGJkODJmM2FiYmQwMjc2MWZkODc5ZjI3ZWUxYzliODhjNzA1YWUwOTgxNmI4NzZjYmIyMDBmMjE4Nzg3MGM2YzUwZTJlN2ExMWI3ZDE3MzgxYjM0YTYwOTUwZDE5ZjE5Zjg1N2RlOTdhMGFiM2ZiNzNiNjZmMDlkM2RjY2U3NzlkMzIyZGJmZTRmYyIsImVtYWlsIjoienBqdW1wZXJAZ21haWwuY29tIn0.Yh7uskjLtipk8tz91oAnvQ4mGfWR1597IHEcMM7JBxg",
        'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36",
        'Accept-Encoding': "gzip, deflate, br",
        'Accept-Language': "zh-CN,zh;q=0.9,en;q=0.8,ja;q=0.7,pt;q=0.6",
        'cache-control': "no-cache",
    }
    DOMAIN_URL = 'https://apiv2.aminer.cn/magic'

    def __init__(self):
        pass

    @classmethod
    def update_token(cls):
        aminer_login_url = 'https://api.aminer.cn/api/auth/signin'
        headers = {
            'Accept': "application/json, text/plain, */*",
            'Content-Type': "application/json",
            'Origin': "https://www.aminer.cn",
            'Referer': "https://www.aminer.cn/login?callback=",
            'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.109 Safari/537.36",
            'cache-control': "no-cache",
        }
        data = {
            "email": "liangtengfei09@mails.ucas.ac.cn",
            "password": "test@test",
            "persist": True,
            "src": "aminer"}
        try:
            # logger.info('getting new token')
            rs = rq.post(aminer_login_url, data=json.dumps(data), headers=headers)
            token = rs.json()['token']
        except Exception as e:
            # logger.info(e)
            token = None
        return token

    @classmethod
    def person_pubs(cls, pid, start=0, size=20):
        url = 'https://api.aminer.cn/api/person/pubs/{}/all/year/{}/{}'.format(pid, start, size)
        # logger.info(url)
        data = rq.get(url, headers=cls.headers)
        rs = []
        for p in data.json():
            rs.append({
                'title': p.get('title'),
                'title_zh': p.get('title_zh'),
                'year': p.get('year'),
                'authors': [tmp['name'] for tmp in p.get('authors', []) if 'name' in tmp],
            })

            if not rs[-1]['title']:
                rs[-1]['title'] = rs[-1]['title_zh']
        return rs

    @classmethod
    def person_pubs_all_multi(cls, pid, size=100, num_threads=16):
        pub_num = 0
        try:
            pub_num = cls.person_pubs_stats(pid).get('count', 0)
        except Exception as e:
            logRecord('fail to get pubs num: {}'.format(e), 'error')
        p = multiprocessing.Pool(num_threads)
        start = 0
        rs = []
        while start < pub_num:
            res = p.apply_async(cls.person_pubs, kwds=dict(pid=pid, start=start, size=size))
            rs.append(res)
            start += size
        p.close()
        p.join()
        pubs = []
        for r in rs:
            try:
                pubs.extend(r.get())
            except Exception as e:
                logRecord(str(e), 'error')
        return pubs

    @classmethod
    def person_pubs_all(cls, pid, size=100):
        rs = [0]
        start = 0
        while True:
            data = cls.person_pubs(pid, start=start, size=size)
            # time.sleep(np.random.randint(20, 50) / 100)
            if data:
                if data[-1] == rs[-1]:
                    break
                rs.extend(data)
                start += size
            else:
                break
        return rs[1:]

    @classmethod
    def get_paper_with_keyword(cls, keyword, dic={}, key=None, size=20, limit_num=5):
        url = cls.DOMAIN_URL + '?a=SEARCH__search.search___'
        json_data = [{"action": "search.search",
                      "parameters": {"offset": 0, "size": size, "searchType": "all", "switches": ["lang_zh"],
                                     "query": keyword}, "schema": {
                "publication": ["id", "year", "title", "title_zh", "abstract", "abstract_zh", "authors", "authors._id",
                                "authors.name", "authors.name_zh", "num_citation", "venue.info.name",
                                "venue.volume", "venue.info.name_zh"]}}]
        resp = rq.post(url, json=json_data, headers=cls.headers)
        if resp.status_code == 200:
            try:
                data = resp.json()['data'][0]
                if data['succeed']:
                    l_set = []
                    items = []
                    for item in data['items']:
                        title = item.get('title') or item.get('title_zh', '')
                        title = remove_symbol_nospace(title)
                        if title not in l_set:
                            items.append(item)
                            l_set.append(title)
                        if len(items) == limit_num:
                            break
                    if key:
                        dic[key] = items
                    else:
                        return items
                else:
                    return []
            except Exception as e:
                logRecord(str(e), 'error')
                if key:
                    dic[key] = []
                else:
                    return []
        return []

    @classmethod
    def get_person_with_keyword(cls, keyword, dic={}, key=None, size=20, limit_num=5):
        url = cls.DOMAIN_URL + '?a=SEARCH__person.SearchPersonWithDSL___'
        json_data = [{"action": "person.SearchPersonWithDSL",
                      "parameters": {"offset": 0, "size": size, "query": keyword, "sort": "h_index"},
                      # "aggregation": ["gender", "h_index", "nation", "lang"]},
                      "schema": {
                          "person": ["id", "name", "name_zh", "avatar", "tags", "tags_translated_zh",
                                     {"profile": ["position", "position_zh", "affiliation", "affiliation_zh"]}, {
                                         "indices": ["hindex", "gindex", "pubs", "citations"]}]}}]
        resp = rq.post(url, json=json_data)
        if resp.status_code == 200:
            try:
                data = resp.json()['data'][0]
                if data['succeed']:
                    items = []
                    for item in data['items']:
                        pro = item.get('profile', {})
                        if pro.get('affiliation') or pro.get('affiliation_zh') or pro.get('org') or pro.get('org_zh'):
                            items.append(item)
                        if len(items) == limit_num:
                            break
                    if key:
                        dic[key] = items
                    else:
                        return items
                else:
                    logRecord(data['succeed'], 'debug')
                    logRecord(data, 'debug')
                    return []
            except Exception as e:
                logRecord(str(e), 'error')
                if key:
                    dic[key] = []
                else:
                    return []
        logRecord(resp.status_code, 'debug')
        return []

    @classmethod
    def person_info(cls, pid):
        url = 'https://api.aminer.cn/api/person/summary/{}'.format(pid)
        logRecord(url, 'debug')
        data = rq.get(url, headers=cls.headers).json()
        name_en = data.get('name')
        name_zh = data.get('name_zh')
        aff = data.get('aff')
        tag = data.get('tags')
        rs = {
            'name_en': name_en,
            'name_zh': name_zh,
            'aff': aff,
            'tags': tag,
        }
        return rs

    # shixw 获取查询对象的id
    @classmethod
    def person_pid(cls, person_name, org_name):
        url = 'https://api.aminer.cn/api/search/person/advanced?name={}&org={}&size=20&sort=relevance'.format(
            person_name, org_name)
        logRecord(url, 'debug')
        try:
            data = rq.get(url, headers=cls.headers).json()
            return (data["result"][0]["id"])
        except Exception:
            return None

    @classmethod
    def person_pid_post(cls, person_name):
        headers2 = {
            'Accept': "application/json"
        }

        url = "https://apiv2.aminer.cn/magic?a=SEARCH__person.SearchPersonWithDSL___"
        body_json = json.dumps([{"action": "person.SearchPersonWithDSL",
                                 "parameters": {"offset": 0, "size": 5, "name": person_name},
                                 "schema": {"person": ["id"]}}])
        try:
            # data = rq.post(url, body_json,headers=cls.headers).json()
            data = rq.post(url, body_json, headers=headers2).json()
            return data["data"][0]["items"][0]["id"]
        except Exception:
            return None

    # 返回图片url
    @classmethod
    def person_image_url(cls, pid=None):
        if pid:
            url = 'https://api.aminer.cn/api/person/summary/{}'.format(pid)
            logRecord(url, 'debug')
            summary = rq.get(url, headers=cls.headers).json()
        else:
            return ""
        return summary.get("avatar", "")

    @classmethod
    def name_aff(cls, pid=None, summary=None):
        if summary:
            pass
        elif pid:
            url = 'https://api.aminer.cn/api/person/summary/{}'.format(pid)
            logRecord(url, 'debug')
            summary = rq.get(url, headers=cls.headers).json()
        else:
            return {}
        aff_en = summary.get('aff', {}).get('desc', '')
        aff_zh = summary.get('aff', {}).get('desc_zh', '')
        name_en = summary.get('name', '')
        name_zh = summary.get('name_zh', '')
        rs = {
            'aff': aff_en or aff_zh,
            'name': name_en or name_zh,
            'names': [name_en, name_zh],
            'affs': [aff_en, aff_zh],
        }
        return rs

    @classmethod
    def person_pubs_stats(cls, pid):
        url = 'https://api.aminer.cn/api/person/pubs/{}/stats'.format(pid)
        # logger.info(url)
        data = rq.get(url, headers=cls.headers).json()
        # count = sum([tmp['size'] for tmp in data['years']])
        count = sum([tmp['size'] for tmp in data['ncites']])
        data['count'] = count
        return data

    @classmethod
    def person_summary(cls, pid):
        url = "https://api.aminer.cn/api/person/summary/{}".format(pid)
        # logger.info(url)
        # data = rq.get(url).json()
        try:
            data = rq.get(url, headers=cls.headers).json()
            return data
        except Exception as e:
            logRecord(str(e), 'error')
            return None

    @classmethod
    def person_identity(cls, pid):
        smy = cls.person_summary(pid)
        num_cit = smy['indices'].get('num_citation', 0)
        num_pub = smy['indices'].get('num_pubs', 0)
        g_index = smy['indices'].get('g_index', 0)
        h_index = smy['indices'].get('h_index', 0)

        pubs = cls.person_pubs_stats(pid)
        years = [int(tmp['year']) for tmp in pubs['years']]
        years = max(years) - min(years) + 1

        rs = {
            'pc': num_pub,
            'cn': num_cit,
            'hi': h_index,
            'gi': g_index,
            'year_range': years,
        }
        return rs

    @classmethod
    def person_picture(cls, pid):
        data = cls.person_summary(pid=pid)
        pic_url = data.get('avatar')
        if pic_url:
            url = 'http:{}'.format(pic_url)
        else:
            url = None
        return url

    @classmethod
    def search_paper_with_title(cls, title, year_limit=None):
        url = cls.DOMAIN_URL + '?a=SEARCH__publication7.SearchPubsCommon___'
        json_data = [{"action": "publication7.SearchPubsCommon",
                      "parameters": {"offset": 0, "size": 20, "searchType": "all", "switches": ["lang_zh"],
                                     "query": title}, "schema": {
                "publication": ["id", "year", "title", "title_zh", "abstract", "abstract_zh", "authors", "authors._id",
                                "authors.name", "keywords", "authors.name_zh", "num_citation",
                                "venue.info.name", "venue.volume", "venue.info.name_zh", "venue.info.publisher",
                                "venue.issue", "pages.start", "pages.end", "doi"]}}]
        resp = rq.post(url, headers=cls.headers, json=json_data)
        this_year = datetime.now().year
        if type(year_limit) == int:
            year_threshold = this_year - year_limit
        else:
            year_threshold = 0
        if resp.status_code == 200:
            for paper in resp.json()['data'][0].get('items', []):
                if match_aminer_paper(title, paper.get('title', '')) and paper.get('year', 0) >= year_threshold:
                    return paper
        return None

    @classmethod
    @timing
    def get_person_with_id(cls, ids, profile_detail=True):
        json_data = [
            {
                "action": "search.Search",
                "eventName": "search",
                "parameters": {
                    "ids": ids,
                    "offset": 0,
                    "size": 100,
                    "searchType": "all"
                },
                "primarySchema": "person",
                "schema": {
                    "person": [
                        "id",
                        "name",
                        "name_zh",
                        "avatar",
                        "tags",
                        "tags_translated_zh",
                        {
                            "indices": [
                                "hindex",
                                "pubs",
                                "citations"
                            ]
                        }
                    ]
                }
            }
        ]
        if profile_detail:
            json_data[0]['schema']['person'].append('profile')
        else:
            json_data[0]['schema']['person'].append({"profile": ["position", "position_zh", "affiliation", "affiliation_zh", "academic_type"]})
        res = rq.post(cls.DOMAIN_URL, headers=cls.headers, json=json_data)
        if res.status_code == 200:
            if res.json()['data'][0].get('items', []):
                return res.json()['data'][0]['items']
        return None


if __name__ == '__main__':


    test = 11
    if test == 1:
        # identity feature
        tpid = '53f47977dabfae8a6845b643'
        trs = Aminer.person_identity(tpid)
        print(trs)
    elif test == 2:
        # base info
        tpid = '542a5365dabfae646d550260'
        tpid = '53f4442adabfaedd74de569d'
        tpid = '542c3722dabfae2b4e1f1f9b'
        tpid = '53f46a3edabfaee43ed05f08'
        trs = Aminer.person_info(tpid)
        print(trs)
    elif test == 3:
        tpid = '53f46a3edabfaee43ed05f08'
        trs = Aminer.person_pubs_stats(tpid)
        print(trs)
    elif test == 4:
        tpid = '53f46a3edabfaee43ed05f08'
        tpid = '5619120945cedb3397d40ba0'
        tpid = '53f46a3edabfaee43ed05f08'
        # rs = Aminer.person_pubs(pid, start=300, size=100)
        trs1 = Aminer.person_pubs_all(tpid, size=50)
        print(len(trs1))
        with open('test50.json', 'w') as f:
            for tmp in trs1:
                f.write(json.dumps(tmp, ensure_ascii=False) + '\n')
        trs2 = Aminer.person_pubs_all(tpid, size=20)
        with open('test20.json', 'w') as f:
            for tmp in trs2:
                f.write(json.dumps(tmp, ensure_ascii=False) + '\n')
        print(len(trs2))
    elif test == 5:
        tpid = '53f46a3edabfaee43ed05f08'
        # tpid = '53f447bddabfaee43ec832a8'
        trs = Aminer.person_pubs_stats(tpid)
        print(trs)
    elif test == 6:
        tpid = '53f46a3edabfaee43ed05f08'
        # tpid = '5619120945cedb3397d40ba0'
        tpid = '53f42f36dabfaedce54dcd0c'
        trs = Aminer.person_pubs_all_multi(pid=tpid, size=100)
        print(trs, len(trs))
    elif test == 7:
        tpid = '53f42f36dabfaedce54dcd0c'
        tpid = '53f43df8dabfaee1c0ad632e'
        trs = Aminer.person_summary(pid=tpid)
        print(trs['name'])
        print(trs['contact'])
    elif test == 8:
        trs = Aminer.update_token()
        print(trs)
    elif test == 9:
        ret = Aminer.get_person_with_keyword('钟南山')
        print(ret)

    elif test == 10:
        # ret = Aminer.get_person_with_id(["53f593a8dabfaee1f3f8045b"])
        # print(ret)
        this_year = datetime.now().year
        print(this_year, type(this_year))
    elif test == 11:
        pid = ['54403d73dabfae7d84b7aeec']
        ret = Aminer.get_person_with_id(pid, profile_detail=True)
        print(ret)
