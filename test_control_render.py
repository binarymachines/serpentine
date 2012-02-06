#!/usr/bin/python

import os, sys
from db import *
import jinja2
from content import *



myDB = MySQLDatabase('localhost', 'bifrost')
myDB.login('dtaylor', 'notobvious')
pMgr = PersistenceManager(myDB)



currentDir = os.getcwd()
bootstrapDir = os.path.join(currentDir, "bootstrap")
env = jinja2.Environment(loader = jinja2.FileSystemLoader(bootstrapDir))
templateMgr = JinjaTemplateManager(env)



select = SelectResponder('distributors', 'distributor_id')
radio = RadioGroupResponder('vod_categories', 'vod_category_id')

data = select._respond(pMgr)

#print data['menu']


templateObject = templateMgr.getTemplate('select_control.html')
print templateObject.render(data)
