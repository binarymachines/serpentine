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


"""
myDB = MySQLDatabase('localhost', 'bifrost')
myDB.login('dtaylor', 'notobvious')
pMgr = PersistenceManager(myDB)




configFile = open('serpentine_test.conf')
config = yaml.load(configFile.read())

factory = DataSourceFactory()
dsr = DataSourceRegistry()

for sourceName in config['datasources']:
    params = config['datasources'][sourceName]
    print 'The parameters for the %s datasource are: %s' % (sourceName, params)

    sourceType = config['datasources'][sourceName]['type']
    print "Creating a datasource of type: %s..." % sourceType
    newDataSource = factory.createDataSource(sourceType, **params)
    dsr.addDataSource(newDataSource, sourceName)



cFactory = ControlFactory()

myControls = {}

for control in config['controls']:
    params = config['controls'][control]
    controlType = config['controls'][control]['type']
    print 'Creating an HTML control of type: %s...' % controlType
    newControl = cFactory.createControl(controlType, dsr, **params)
    myControls[control] = newControl

"""


print 'Loading control class...'

controlTypeName = 'Select'
typeKey = '%sControl' % controlTypeName
fqControlClassName = '.'.join(['content', typeKey])
controlClass = ClassLoader().loadClass(fqControlClassName)


print 'Control class %s loaded.' % controlClass.__name__


