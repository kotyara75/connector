from marshmallow import Schema, fields

from requests.auth import AuthBase

from connector.config import Config

import requests

config = Config()


class StorageSchema(Schema):
    usage = fields.Int(load_only=True)
    limit = fields.Int()


class BoxAuth(AuthBase):
    def __init__(self, token):
        if not token:
            # headers = {'user-agent': 'my-app/0.0.1'}
            auth_request_data = {
                    "grant_type": "client_credentials",
                    "client_id": config.box_reseller_client_id,
                    "client_secret": config.box_reseller_client_secret,
                    "box_subject_id": config.box_reseller_id,
                    "box_subject_type": "reseller",
                }

            r = requests.post(config.box_oauth_baseurl + "token", data=auth_request_data)

            token = r.json()["access_token"]

        self.token = token

    def __call__(self, r):
        r.headers['Authorization'] = 'Bearer {}'.format(self.token)
        return r
