import logging
from flask import g, make_response

from flask_restful import reqparse

from connector.config import Config
from connector.client.user import User as BoxUser
from connector.client.client import Client
from connector.utils import escape_domain_name

from . import (ConnectorResource, Memoize, OA, OACommunicationException,
               parameter_validator, urlify)


logger = logging.getLogger(__file__)
config = Config()


@Memoize
def get_enterprise_id_for_tenant(tenant_id):
    tenant_resource = OA.get_resource(tenant_id)
    if 'tenantId' not in tenant_resource:
        raise KeyError("tenantId property is missing in OA resource {}".format(tenant_id))
    enterprise_id = tenant_resource['tenantId']
    return None if enterprise_id == 'TBD' else enterprise_id

def make_user(client, oa_user):
    email = oa_user['email']
    name = oa_user['fullName']
    admin = oa_user['isAccountAdmin']
    phone = oa_user['telWork'] if admin else None
    if admin:
        oa_address = oa_user['addressPostal']
        address = '{},{},{},{},{}'.format(oa_address['streetAddress'],oa_address['locality'],oa_address['region'],
                                      oa_address['postalCode'],oa_address['countryName'])
    else:
        address = None

    user = BoxUser(client=client, login=email, name=name, admin=admin, phone=phone, address=address)
    return user


def make_default_user(client):
    email = 'admin@{}.io'.format(urlify(client.name))
    name = '{} Admin'.format(client.name)
    admin = True

    user = BoxUser(client=client, login=email, name=name, admin=admin)
    return user


class TenantList(ConnectorResource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('aps', dest='aps_id', type=parameter_validator('id'),
                            required=True,
                            help='Missing aps.id in request')
        parser.add_argument(config.users_resource, dest='users_limit',
                            type=parameter_validator('limit'), required=False)
        parser.add_argument('oaSubscription', dest='sub_id', type=parameter_validator('aps', 'id'),
                            required=True,
                            help='Missing link to subscription in request')
        parser.add_argument('oaAccount', dest='acc_id', type=parameter_validator('aps', 'id'),
                            required=True,
                            help='Missing link to account in request')

        args = parser.parse_args()

        company_name = OA.get_resource(args.acc_id)['companyName']
        sub_id = OA.get_resource(args.sub_id)['subscriptionId']
        company_name = '{}-sub{}'.format(company_name if company_name else 'Unnamed', sub_id)

        client = Client(g.reseller, name=company_name, users_limit=args.users_limit)

        admins = OA.send_request('GET',
                                 '/aps/2/resources?implementing(http://parallels.com/aps/types/pa/admin-user/1.0)',
                                 impersonate_as=args.aps_id)
        if not admins:
            raise KeyError("No admins in OA account {}".format(args.acc_id))

        user = make_user(client, admins[0])

#        user = make_default_user(client)

        try:
            client.create(user)
        except Exception as e:
            logger.info("Exception during account creation: %s", e)
            # We don't support two subscriptions for one box account for now, skip it.
            client.enterprise_id = 'SECOND'
        finally:
            g.enterprise_id = client.enterprise_id
            return {'tenantId': client.enterprise_id}, 201


class Tenant(ConnectorResource):
    def get(self, tenant_id):
        enterprise_id = g.enterprise_id = get_enterprise_id_for_tenant(tenant_id)
        client = Client(g.reseller, enterprise_id = enterprise_id)
        client.refresh()
        return {
            config.users_resource: {
                'usage': client.users_amount
            }
        }

    def put(self, tenant_id):
        parser = reqparse.RequestParser()
        parser.add_argument(config.users_resource, dest='users_limit',
                            type=parameter_validator('limit'), required=False,
                            help='Missing {} limit in request'.format(config.users_resource))
        args = parser.parse_args()
        enterprise_id = g.enterprise_id = get_enterprise_id_for_tenant(tenant_id)
        if enterprise_id == 'SECOND':
            return {}

        if args.users_limit:
            client = Client(g.reseller, enterprise_id=enterprise_id,
                            users_limit=args.users_limit)
            client.update()
        return {}

    def delete(self, tenant_id):
        enterprise_id = g.enterprise_id = get_enterprise_id_for_tenant(tenant_id)
        if enterprise_id != 'SECOND':
            client = Client(g.reseller, enterprise_id=enterprise_id)
            client.delete()
        return None, 204


class TenantDisable(ConnectorResource):
    def put(self, tenant_id):
        # Not supported by the service yet
        return {}


class TenantEnable(ConnectorResource):
    def put(self, tenant_id):
        # Not supported by the service yet
        return {}


class TenantAdminLogin(ConnectorResource):
    def get(self, tenant_id):
        login_link = 'https://app.box.com/'
        response = make_response(login_link)
        response.headers.add('Content-Type', 'text/plain')
        return response


class TenantUserCreated(ConnectorResource):
    def post(self, oa_tenant_id):
        return {}
        enterprise_id = get_enterprise_id_for_tenant(oa_tenant_id)
        if enterprise_id:
            # existing tenant, do  nothing, user will be created in the user request
            g.enterprise_id = enterprise_id
            return {}

        #  Enterprise creation has been delayed until first user provisioning, let's do it now
        parser = reqparse.RequestParser()

        parser.add_argument('tenant', dest='oa_sub_id', type=parameter_validator('aps', 'subscription'),
                            required=True,
                            help='Missing link to subscription in request')
        parser.add_argument('user', dest='oa_user_id', type=parameter_validator('aps', 'id'),
                            required=True,
                            help='Missing link to users list in request')

        args = parser.parse_args()

        oa_user = OA.get_resource(args.oa_user_id)
        sub_id = OA.get_resource(args.oa_sub_id)['subscriptionId']
        oa_tenant = OA.get_resource(oa_tenant_id)
        oa_account = OA.get_resource(oa_tenant['oaAccount']['aps']['id'])

        company_name = oa_account['companyName']
        company_name = '{}-sub{}'.format(company_name if company_name else 'Unnamed', sub_id)
        users_limit = oa_tenant[config.users_resource]['limit']

        client = Client(g.reseller, name=company_name, users_limit=users_limit)
        user = make_user(client, oa_user)
        client.create(user)
        g.enterprise_id = enterprise_id = client.enterprise_id
        # todo: save tenantId
        return {}

class TenantUserRemoved(ConnectorResource):
    def delete(self, tenant_id, user_id):
        return {}
