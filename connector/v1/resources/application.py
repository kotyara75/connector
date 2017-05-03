import pkg_resources

from flask import g

from flask_restful import abort, reqparse

from connector.client.reseller import Reseller

from . import ConnectorResource, Memoize, parameter_validator

env = pkg_resources.Environment()
res = env._distmap.get('box-connector', [None])[0]
version = res.version if res else ''

class HealthCheck(ConnectorResource):
    def get(self):
        return {'status': 'ok',
                'version': version}


class ApplicationList(ConnectorResource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('aps', dest='aps_type', type=parameter_validator('type'),
                            required=True, help='No APS type specified')
        parser.add_argument('aps', dest='aps_id', type=parameter_validator('id'),
                            required=True, help='No APS id specified')
        args = parser.parse_args()
#        g.reseller.create()
        return {'aps': {'type': args.aps_type, 'id': args.aps_id}}, 201


class Application(ConnectorResource):
    def delete(self, app_id):
#        if g.reseller.reseller_name != app_id:
#            abort(403)
#        g.reseller.delete()
        return {}, 204


class ApplicationUpgrade(ConnectorResource):
    def post(self, app_id):
        return {}


class ApplicationTenantNew(ConnectorResource):
    def post(self, app_id, tenant_id=None):
        return {}


class ApplicationTenantDelete(ConnectorResource):
    def delete(self, app_id, tenant_id=None):
        return {}
