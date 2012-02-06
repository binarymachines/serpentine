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



myDB = MySQLDatabase('localhost', 'bifrost')
myDB.login('dtaylor', 'notobvious')
pMgr = PersistenceManager(myDB)




configFile = open('serpentine_test.conf')
config = yaml.load(configFile.read())

factory = DataSourceFactory()
myDataSources = {}

for source in config['datasources']:
    params = config['datasources'][source]
    print params

    
    sourceType = config['datasources'][source]['type']
    print "Creating a datasource of type: %s..." % sourceType
    newDataSource = factory.createDataSource(sourceType, **params)
    myDataSources[source] = (newDataSource)



print myDataSources
    
scheduleDataSource = myDataSources['distributors']
scheduleDataSource.load(pMgr)
print scheduleDataSource()
 






