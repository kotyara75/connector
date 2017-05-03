import re
import json

import requests

try:
    from functools import reduce
except ImportError:
    pass

try:
    from urllib.parse import urljoin
except ImportError:
    from urlparse import urljoin

from flask import g, request

from flask_restful import Resource

from slumber.exceptions import HttpClientError, HttpServerError


def parameter_validator(*args):
    def extract_params(where, *args):
        def extract_one(where, what):
            if what not in where:
                raise ValueError("Missing {} in request".format(what))
            return where[what]

        return reduce(extract_one, args, where)

    def validate(where):
        return extract_params(where, *args)

    return validate


def urlify(data):
    return re.sub(r'\s+', '-',
                  re.sub(r'[^\w\s]', '', data))


def make_error(e):
    return {'message': e.response.text.strip('"')}, e.response.status_code


class ConnectorResource(Resource):
    def dispatch_request(self, *args, **kwargs):
        try:
            return super(ConnectorResource, self).dispatch_request(*args, **kwargs)
        except (HttpClientError, HttpServerError) as e:
            return make_error(e)


class OACommunicationException(Exception):
    def __init__(self, resp):
        msg = "Request to OA failed. OA responded with code {}\n{}".format(resp.status_code,
                                                                           resp.text)
        super(OACommunicationException, self).__init__(msg)


class OA(object):
    request_timeout = 50

    @staticmethod
    def get_resource(resource_id, transaction=True, retry_num=10):
        rql_request = 'aps/2/resources/{}'.format(resource_id)
        return OA.send_request('get', rql_request, transaction=transaction, retry_num=retry_num)

    @staticmethod
    def get_resources(rql_request, transaction=True, retry_num=10):
        return OA.send_request('get', rql_request, transaction=transaction, retry_num=retry_num)

    @staticmethod
    def send_request(method, path, body=None, transaction=True, impersonate_as=None, retry_num=10):
        oa_uri = request.headers.get('aps-controller-uri')
        url = urljoin(oa_uri, path)

        headers = {'Content-Type': 'application/json'}
        if impersonate_as:
            headers['aps-resource-id'] = impersonate_as
        if transaction:
            headers['aps-transaction-id'] = request.headers.get('aps-transaction-id')

        data = None if body is None else json.dumps(body)

        retry_num = retry_num if retry_num > 0 else 1

        while retry_num > 0:
            retry_num -= 1
            resp = requests.request(
                method=method,
                url=url,
                data=data,
                headers=headers,
                auth=g.auth,
                timeout=OA.request_timeout,
                verify=False
            )

            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code != 400:
                raise OACommunicationException(resp)

        raise OACommunicationException(resp)


class Memoize(object):
    def __init__(self, function):
        self.function = function
        self.memoized = {}

    def __call__(self, *args):
        if args not in self.memoized:
            self.memoized[args] = self.function(*args)
        return self.memoized[args]
