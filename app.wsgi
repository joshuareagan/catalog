#!/usr/bin/python3
import sys
import logging
logging.basicConfig(stream=sys.stderr)
sys.path.insert(0,"/var/www/catalog/")

from cities import app as application
application.secret_key = 'This is not the most secure key ever written.'
