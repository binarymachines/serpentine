import sys, os

os.chdir(os.path.dirname(__file__))
sys.path = [os.path.dirname(__file__)] + sys.path

import bottle

from beaker.middleware import SessionMiddleware
from bottle import debug, route, template, install, default_app
from environment import *
from reporting import *
from events import *

# Heavyweight init logic and service objects,
# particular to the NetPath family
from netpath import *

npPlugin = NetPathStartupPlugin('{% web_app_name %}.conf')
install(npPlugin)


import main # This loads your application

debug(True)

session_opts = {
    "session.type": "file",
    'session.cookie_expires': True,
    'session.auto': True,
    'session.data_dir': "cache",
}


application = SessionMiddleware(bottle.default_app(), session_opts)
