import json
import time
from bs4 import BeautifulSoup
from bs4 import NavigableString

from apps.common.requests_util import Requests


class FlightInfo(Requests):
    URL = {
        "variflight":
            {
                "url": "http://www.variflight.com/flight/fnum/{}.html?AE71649A58c77&fdate={}",
                'method': 'get'
            },
        "trip":
            {
                "url": "https://flights.ctrip.com/actualtime/fno--{}-{}.html",
                'method': 'get'
            },
        "flightadsb":
            {
                "url": "https://adsbapi.variflight.com/adsb/index/advancedSearch?lang=zh_CN&token=e0542734e9698138300867fbef07eb13",
                'method': 'post'
            }
    }

    def __init__(self, flynum, flydate):
        self.flynum = flynum
        self.flydate = flydate
        super(FlightInfo, self).__init__()

    def request_html(self, url, method='get', data=None):
        if method == 'get':
            resp = self.get(url.format(self.flynum, self.flydate))
        else:
            resp = self.post(url, data=data)
        if resp.status_code == 200:
            self.text = resp.text
        else:
            self.text = None

    def crawl(self, source=None):
        if source:
            url = self.URL.get(source, {})
            if url:
                if url['method'] == 'get':
                    self.request_html(url['url'])
                else:
                    param = {'searchText': self.flynum, 'searchDate': self.flydate, 'timeZone': '-28800'}
                    self.request_html(url['url'], method='post', data=param)
                ret = getattr(self, f'{source}_parse_html')()
                return ret
        else:
            for key, url in self.URL.items():
                if url['method'] == 'get':
                    self.request_html(url['url'])
                else:
                    param = {'searchText': self.flynum, 'searchDate': self.flydate, 'timeZone': '-28800'}
                    self.request_html(url['url'], method='post', data=param)
                ret = getattr(self, f'{key}_parse_html')()
                if ret:
                    return ret
        return {}

    def variflight_parse_html(self):
        try:
            soup = BeautifulSoup(self.text, 'html.parser')
            flight_li = soup.select('#list li')
            flight_spans = flight_li[-1].select('div.li_com span')
            # flight_spans = soup.select('#list div.li_com span')

            flyinfo = flight_spans[0].text.replace('\n', ' ').strip()
            dplantime = flight_spans[1].text.strip()
            origin = flight_spans[3].text.strip()
            aplantime = flight_spans[4].text.strip()
            destination = flight_spans[6].text.strip()
            status = flight_spans[8].text.strip()
            ret = {
                'flyinfo': flyinfo,
                'dplan': dplantime,
                'origin': origin,
                'aplan': aplantime,
                'destination': destination,
                'status': status
            }
            return ret
        except Exception as e:
            return {}

    def trip_parse_html(self):
        try:
            soup = BeautifulSoup(self.text, 'html.parser')
            flight_divs = soup.select('#base_bd div.detail-box > .detail-info > div')
            flyinfo = [i.text.strip() for i in flight_divs[0].contents if type(i) != NavigableString and i.text.strip()][0]\
                      + ' ' + self.flynum
            detail_fly = flight_divs[1].find('div', {'class': 'detail-fly'})
            dplan = detail_fly.find('div', class_='inl departure').find('p', class_='time').text
            status = detail_fly.find('div', class_='inl between').text
            aplan = detail_fly.find('div', class_='inl arrive').find('p', class_='time').text
            detail_route = flight_divs[1].find('div', {'class': 'detail-fly detail-route'})
            origin = ' '.join([i.strip() for i in detail_route.find('div', class_='inl departure').find('p').text.split(' ') if i.strip()])
            destination = ' '.join([i.strip() for i in detail_route.find('div', class_='inl arrive').find('p').text.split(' ') if i.strip()])
            ret = {
                'flyinfo': flyinfo,
                'dplan': dplan,
                'origin': origin,
                'aplan': aplan.strip(),
                'destination': destination,
                'status': status.strip()
            }
            return ret
        except Exception as e:
            return {}

    def flightadsb_parse_html(self):
        try:
            print(self.text)
            data = json.loads(self.text)['data'][0]
            ret = {
                'flyinfo': f"{data['fnum']}/{data['fnum3']}",
                'dplan': time.strftime('%Y-%m-%d %H:%M', time.localtime(data['scheduledDeptime'])),
                'origin': data['forgAptCname'],
                'origin_en': data['forgAptName'],
                'origin_short': data['forg'],
                'aplan': time.strftime('%Y-%m-%d %H:%M', time.localtime(data['scheduledArrtime'])),
                'destination': data['fdstAptCname'],
                'destination_en': data['fdstAptName'],
                'destination_short': data['fdst'],
            }
            return ret
        except Exception as e:
            print(str(e))
            return {}

if __name__ == '__main__':
    ret = FlightInfo('CZ324', '20200322').crawl('variflight')
    print(ret)
    # import requests
    # param = {'searchText': 'JL772', 'searchDate': '20200314', 'timeZone': '-28800'}
    # res = requests.post('https://adsbapi.variflight.com/adsb/index/advancedSearch?lang=zh_CN&token=e0542734e9698138300867fbef07eb13', data=param)
    # print(res.status_code)
    # print(res.text)

