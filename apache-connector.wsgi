import sys
sys.path.insert(0, '/var/www/boxconnector')

import os
os.environ['CONFIG_FILE'] = '/var/www/boxconnector/config.json'

from connector.app import app as application
