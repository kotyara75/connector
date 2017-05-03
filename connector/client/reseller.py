import slumber

from marshmallow import Schema, fields, post_load, pre_dump

from slumber.exceptions import HttpNotFoundError

from connector.client import BoxAuth, StorageSchema
from connector.client import config


class Reseller(object):
    token = None


    def __init__(self, token=None):
        self.token = token

    def api(self, token=None):
        token = token if token else self.token
        auth = BoxAuth(token)
        self.token = auth.token
        return slumber.API(config.box_baseurl, auth=auth)

    def __repr__(self):
        return '<Reseller>'

    def refresh(self):
        self.api()