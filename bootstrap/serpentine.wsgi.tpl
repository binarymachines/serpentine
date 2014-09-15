import sys, os

sys.path = ['/opt/local/apache2/htdocs/wellspring'] + sys.path
sys.path.insert(0, '/Library/Python/2.6/site-packages/bottle-0.8.5-py2.6.egg-info')
sys.path.insert(0, '/Library/Python/2.6/site-packages/SQLAlchemy-0.6.6-py2.6.egg')
sys.path.insert(0, '/Library/Python/2.6/site-packages/MySQL_python-1.2.3c1-py2.6-macosx-10.6-universal.egg')
sys.path.insert(0, '/Library/Python/2.6/site-packages/ipython-0.10.2-py2.6.egg')
sys.path.insert(0, '/Library/Python/2.6/site-packages/setuptools-0.6c12dev_r88795-py2.6.egg')
sys.path.insert(0, '/Library/Python/2.6/site-packages/Beaker-1.5.4-py2.6.egg')
sys.path.insert(0, '/Library/Python/2.6/site-packages/WTForms-0.6.2-py2.6.egg')
sys.path.insert(0, '/Library/Python/2.6/site-packages/Jinja2-2.5.5-py2.6.egg')
sys.path.insert(0, '/opt/local/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages/xlwt-0.7.2-py2.7.egg-info')
os.chdir(os.path.dirname(__file__))

import bottle

from beaker.middleware import SessionMiddleware

from bottle import debug, route, template, install, default_app

from environment import *
from reporting import *
from events import *


# Heavyweight init logic and service objects,
# particular to the NetPath family

from netpath import *

npPlugin = NetPathStartupPlugin('netpath.conf')
install(npPlugin)


import wellspring_main # This loads your application

debug(True)

session_opts = {
    "session.type": "file",
    'session.cookie_expires': True,
    'session.auto': True,
    'session.data_dir': "cache",
}



application = SessionMiddleware(bottle.default_app(), session_opts)