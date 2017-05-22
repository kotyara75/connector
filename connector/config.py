import json
import os
import logging
import sys

logger = logging.getLogger(__file__)
logger.setLevel(logging.DEBUG)
stream = logging.StreamHandler(sys.stdout)
logger.addHandler(stream)

def check_configuration(config):
    for item in (
        'box_baseurl',
        'box_oauth_baseurl',
        'box_reseller_client_id',
        'box_reseller_client_secret',
        'box_reseller_id',
        'oauth_key',
        'oauth_signature',
    ):
        if getattr(config, item).startswith('PUT_HERE_'):
            return False

    return True


class Config(object):
    conf_file = os.environ.get('CONFIG_FILE', './config.json')
    loglevel = None
    users_resource = None
    box_baseurl = None
    box_oauth_baseurl = None
    box_reseller_client_id = None
    box_reseller_client_secret = None
    box_reseller_id = None
    oauth_key = None
    oauth_signature = None
    tenant_type_resource = None
    tenant_type_map = None

    def __init__(self):
        if not Config.users_resource:
            self.load()

    @staticmethod
    def load():
        if not os.path.isfile(Config.conf_file):
            raise IOError("Config file not found: {}".format(Config.conf_file))

        with open(Config.conf_file, 'r') as c:
            config = json.load(c)
            Config.loglevel = config.get('loglevel', 'DEBUG')

            try:
                Config.users_resource = config['users_resource']
                Config.tenant_type_resource = config['tenant_type_resource']
                Config.box_oauth_baseurl = config['box_oauth_baseurl']
                Config.box_baseurl = config['box_baseurl']
                Config.box_reseller_client_id = config['box_reseller_client_id']
                Config.box_reseller_client_secret = config['box_reseller_client_secret']
                Config.box_reseller_id = config['box_reseller_id']
                Config.oauth_key = config['oauth_key']
                Config.oauth_signature = config['oauth_signature']
            except KeyError as e:
                raise RuntimeError(
                    "{} parameter not specified in config.".format(e))

            tmap = {
                0: 'generic_business',
                1: 'generic_enterprise',
                2: 'generic_starter',
                3: 'telstra_business_plus'
            }

            try:
                tmap = config['tenant_types_map']
            except KeyError as e:
                logger.info("Tenant types map is missed in the config file, using default one ({})".format(e))
            finally:
                Config.tenant_type_map = tmap