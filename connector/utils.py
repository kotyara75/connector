import logging
import sys
import json
import re

from flask import g

logger = logging.getLogger(__file__)


class ResellerNameFilter(logging.Filter):
    def filter(self, record):
        record.reseller_name = str(g.reseller_name)
        return True


class ConnectorLogFormatter(logging.Formatter):
    def format(self, record):
        resp = {}
        if isinstance(record.msg, dict):
            resp['message'] = record.msg
        else:
            resp['message'] = record.getMessage()
        resp['time'] = self.formatTime(record, self.datefmt)
        resp['level'] = record.levelname
        resp['reseller_id'] = record.reseller_name
        return json.dumps(resp)


stream = logging.StreamHandler(sys.stdout)
logger.addFilter(ResellerNameFilter())
formatter = ConnectorLogFormatter()
stream.setFormatter(formatter)
logger.setLevel(logging.DEBUG)
logger.addHandler(stream)


def log_request(request):
    logger.info({"type": "request",
                 "app": "box_connector",
                 "method": request.method,
                 "url": request.url,
                 "headers": dict(request.headers),
                 "data": request.data.decode('utf-8')})


def log_response(response):
    logger.info({"type": "response",
                 "app": "box_connector",
                 "status_code": response.status_code,
                 "status": response.status,
                 "headers": dict(response.headers),
                 "data": response.data.decode('utf-8'),
                 "company_id": g.enterprise_id})


def escape_domain_name(name):
    valid_name = re.sub(r'[^a-zA-Z0-9-.]', '-', name)
    valid_name = re.sub(r'(^-+)|(-+$)', '', valid_name)
    return valid_name
