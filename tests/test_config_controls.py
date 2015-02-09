import os
import logging
import yaml

from jinja2 import StrictUndefined
from content import *
from db import *
from events import *
from core import *
from reporting import *

from sqlalchemy.orm import mapper
from sqlalchemy.exc import SQLAlchemyError

from environment import ClassLoader



myDB = MySQLDatabase('localhost', 'samplespace')
myDB.login('dtaylor', 'notobvious')
pMgr = PersistenceManager(myDB)


configFile = open('samplespace.conf')
config = yaml.load(configFile.read())

factory = DataSourceFactory()
dsr = DataSourceRegistry()

print 'Creating datasources...'

for sourceName in config['datasources']:
    params = config['datasources'][sourceName]
    print 'The parameters for the %s datasource are: %s' % (sourceName, params)

    sourceType = config['datasources'][sourceName]['type']
    print "Creating a datasource of type: %s..." % sourceType
    newDataSource = factory.createDataSource(sourceType, 'samplespace_datasources', **params)
    dsr.addDataSource(newDataSource, sourceName)

print 'Done.'


source = dsr.getDataSource('items_in_show_src')
#source.load(pMgr, show_id=2)
print source()


cFactory = ControlFactory()

myControls = {}

for control in config['ui-controls']:
    params = config['ui-controls'][control]
    controlType = config['ui-controls'][control]['type']
    print 'Creating an HTML control of type: %s...' % controlType
    newControl = cFactory.createControl(controlType, dsr, **params)
    myControls[control] = newControl


print 'Loading HTML control...'
ctrl = myControls['items_in_show_grid']

print 'Retrieving data...'

print ctrl._getData(pMgr, show_id=1)

print 'Done.'
