from flask import g, make_response
from flask_restful import reqparse

from connector.config import Config
from connector.client.client import Client
from connector.client.user import User as BoxUser
from connector.v1.resources.tenant import get_enterprise_id_for_tenant, make_user
from . import ConnectorResource, OA, parameter_validator

config = Config()

class UserList(ConnectorResource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('tenant', dest='oa_tenant_id',
                            type=parameter_validator('aps', 'id'),
                            required=True,
                            help='Missing tenant in request')
        parser.add_argument('user', dest='oa_user_id',
                            type=parameter_validator('aps', 'id'),
                            required=True,
                            help='Missing user id in request')
        args = parser.parse_args()

        enterprise_id = g.enterprise_id = get_enterprise_id_for_tenant(args.oa_tenant_id)
        if enterprise_id == 'SECOND':
            # no support for second subscription yet, just skip it
            return {'userId': 'SECOND'}, 201

        client = Client(g.reseller, enterprise_id=enterprise_id)
        client.refresh()

        oa_user = OA.get_resource(args.oa_user_id)

        if client.administered_by['login'] == oa_user['email']:
            # this user has been created as part of tenant registration, just return ID
            return {'userId': client.administered_by['user_id']}, 201

        user = make_user(client, oa_user)
        user.create()
        return {'userId': user.user_id}, 201


class User(ConnectorResource):
    def delete(self, oa_user_service_id):
        user = make_box_user(oa_user_service_id)
        g.enterprise_id = user.client.enterprise_id
        user.delete()

        return {}, 204

    def put(self, oa_user_service_id):
        return {}, 200
        # parser = reqparse.RequestParser()
        # parser.add_argument('???', dest='???', type=str, required=False)
        # args = parser.parse_args()
        # user = make_box_user(oa_user_service_id)
        # user.refresh()
        # client = user.client
        # client.refresh()
        # g.enterprise_id = client.enterprise_id
        # if args.???
        #     user.??? = ???
        # user.update()
        # return {}, 200


class UserLogin(ConnectorResource):
    def get(self, oa_user_service_id):
        user = make_box_user(oa_user_service_id)
        g.enterprise_id = user.client.enterprise_id

        response = make_response(user.login_link())
        response.headers.add('Content-Type', 'text/plain')
        return response


def make_box_user(oa_user_service_id):
    oa_user_service = OA.get_resource(oa_user_service_id)
    oa_user = OA.get_resource(oa_user_service['user']['aps']['id'])
    oa_tenant_id = oa_user_service['tenant']['aps']['id']
    client = Client(reseller=g.reseller, enterprise_id=get_enterprise_id_for_tenant(oa_tenant_id))
    user = BoxUser(client=client, user_id=oa_user['userId'])

    return user
