from flask_restful import Resource

from apps.common import Code, pretty_result, root_parser
from apps.crawler.crawl_flight import FlightInfo
from apps.crawler.interface import crawlExpertsNews, crawlExpertsEnNews
from utils.logger import logRecord
from apps.crawler.mg import magi_selenium


class CrawlFlightView(Resource):
    def __init__(self):
        self.parser = root_parser().copy()

    def get(self):
        self.parser.add_argument("flynum", type=str, location="args", required=True, trim=True)
        self.parser.add_argument("flydate", type=str, location="args", required=True, trim=True)
        args = self.parser.parse_args()
        try:
            data = FlightInfo(args.flynum, args.flydate).crawl()
            return pretty_result(Code.OK, data=data)
        except Exception as e:
            logRecord(f'when request /flight: {str(e)}', 'error', args.debug)
            return pretty_result(Code.UNKNOWN_ERROR, msg=e, debug=args.debug)


class CrawlExpertsNewsView(Resource):
    def __init__(self):
        self.parser = root_parser().copy()

    def post(self):
        self.parser.add_argument("ids", type=list, location="json", required=True, trim=True)
        self.parser.add_argument("kw", type=str, location="json", required=False, trim=True, default=None)
        args = self.parser.parse_args()
        try:
            ret = crawlExpertsNews(args.ids, args.get('kw'))
            return pretty_result(Code.OK, data=ret)
        except Exception as e:
            logRecord(f'when request /experts/news: {str(e)}', 'error', args.debug)
            return pretty_result(Code.UNKNOWN_ERROR, msg=e, debug=args.debug)

class CrawlExpertsEnNewsView(Resource):
    def __init__(self):
        self.parser = root_parser().copy()

    def post(self):
        self.parser.add_argument("ids", type=list, location="json", required=True, trim=True)
        self.parser.add_argument("en_kw", type=str, location="json", required=False, trim=True, default=None)
        args = self.parser.parse_args()
        try:
            ret = crawlExpertsEnNews(args.ids, args.get('en_kw'))
            return pretty_result(Code.OK, data=ret)
        except Exception as e:
            logRecord(f'when request /experts/news-en: {str(e)}', 'error', args.debug)
            return pretty_result(Code.UNKNOWN_ERROR, msg=e, debug=args.debug)

class CrawlMagiView(Resource):
    def __init__(self):
        self.parser = root_parser().copy()

    def post(self):
        self.parser.add_argument("text", type=str, location='json', required=True, trim=True)
        args = self.parser.parse_args()
        try :
            ret = magi_selenium.run(args.get('text'))
            return pretty_result(Code.OK, data=ret)
        except Exception as e:
            logRecord(f'when request /mg/: {str(e)}', 'error', args.debug)
            return pretty_result(Code.UNKNOWN_ERROR, msg=e, debug=args.debug)


