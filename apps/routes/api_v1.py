from flask import Blueprint
from flask_restful import Api
from apps.ncov import views as ncov_views
from apps.crawler import views as crawler_views


api_v1 = Blueprint(name='api_v1', import_name=__name__)

api = Api(api_v1)

api.add_resource(crawler_views.CrawlFlightView, '/flight')
api.add_resource(crawler_views.CrawlExpertsNewsView, '/experts/news')
api.add_resource(crawler_views.CrawlExpertsEnNewsView, '/experts/news-en')
api.add_resource(crawler_views.CrawlMagiView, '/mg')

api.add_resource(ncov_views.PredictView, '/pneumonia/prediction')
api.add_resource(ncov_views.NcovDataView, '/pneumonia/data')
api.add_resource(ncov_views.PredictChangelogView, '/pneumonia/changelog')
api.add_resource(ncov_views.FlightRisk, '/pneumonia/flight-risk')
api.add_resource(ncov_views.NcovDatasetView, '/pneumonia/dataset/<string:id>')
api.add_resource(ncov_views.NcovDatasetsView, '/pneumonia/dataset')
api.add_resource(ncov_views.FeedBackView, '/feedback')
api.add_resource(ncov_views.FeedBackOptView, '/feedback/<string:id>')
api.add_resource(ncov_views.EntityLinkingView, '/pneumonia/entitylink')
api.add_resource(ncov_views.EntityView, '/pneumonia/entity')
api.add_resource(ncov_views.EntityQueryView, '/pneumonia/entityquery')
api.add_resource(ncov_views.UpdateHot, '/pneumonia/view')
api.add_resource(ncov_views.LenovoEntity, '/pneumonia/hit')
api.add_resource(ncov_views.Downloads, '/pneumonia/download')
api.add_resource(ncov_views.Renewal, '/pneumonia/update')
api.add_resource(ncov_views.QA_Answer, '/pneumonia/qa_answer')
api.add_resource(ncov_views.Show_Update, '/pneumonia/show_update')
api.add_resource(ncov_views.QA, '/pneumonia/QA')
