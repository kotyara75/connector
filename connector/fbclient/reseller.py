import slumber

from marshmallow import Schema, fields, post_load, pre_dump

from slumber.exceptions import HttpNotFoundError

from connector.fbclient import FallBallAuth, StorageSchema
from connector.fbclient import config


class ResellerSchema(Schema):
    name = fields.Str()
    rid = fields.Str()
    token = fields.Str()
    clients_amount = fields.Int(load_only=True)
    storage = fields.Nested(StorageSchema)

    @post_load
    def make_reseller(self, data):
        return Reseller(**data)

    @pre_dump
    def dump_reseller(self, data):
        return {k: v for k, v in data.__dict__.items() if v}


class Reseller(object):
    name = None
    rid = None
    token = None
    _clients_amount = None
    storage = None

    def __init__(self, name, rid=None, token=None, clients_amount=None, storage=None):
        self.name = name
        self.rid = rid
        self.token = token
        self._clients_amount = clients_amount
        self.storage = storage

    @property
    def clients_amount(self):
        return self._clients_amount

    def api(self, token=None):
        token = token if token else self.token
        return slumber.API(config.fallball_service_url, auth=FallBallAuth(token))

    def __repr__(self):
        return '<Reseller(name={})>'.format(self.name)

    @property
    def _dump(self):
        return ResellerSchema().dump(self).data

    def create(self):
        api = self.api(config.fallball_service_authorization_token)
        if not self.storage:
            self.storage = {'limit': 1000000}
        result = api.resellers.post(self._dump)
        return result

    def refresh(self):
        api = self.api(config.box_oauth_baseurl)
        try:
            result = api.resellers(self.name).get()
            r = ResellerSchema().load(result).data
            self.__init__(name=r.name, rid=r.rid, token=r.token, clients_amount=r.clients_amount,
                          storage=r.storage)
        except HttpNotFoundError:
            pass

    def delete(self):
        api = self.api(config.fallball_service_authorization_token)
        result = api.resellers(self.name).delete()
        return result

    @staticmethod
    def all():
        api = slumber.API(config.fallball_service_url,
                          auth=FallBallAuth(config.fallball_service_authorization_token))
        result = api.resellers.get()
        resellers = ResellerSchema().load(result, many=True).data
        return resellers
