#!/usr/bin/env python


from environment import *
from businessTypes import *
from db import *
from datetime import *
from plugins import *
from reporting import *
from sqlalchemy import update

from xlwt import *


 


def testReporting(pMgr, className, fieldMap, reportName = 'wsreport'):
    results = pMgr.retrieve_all(className)
    results.fetchone()
    personsTable = pMgr.getTable(className)
    cols = results.metadata.columns
    
    
    for column in cols:
        print column.name
    

def testConnect():
    database = MySQLDatabase('localhost', 'wellspring')
    database.login('dtaylor', 'notobvious')
    pmgr = PersistenceManager(database)
    return pmgr

def testInsert():
    newPost = Post()
    newPost.title = "Hello World"
    newPost.body = "This is the body."
    newPost.created = datetime.now()

def testRetrieveAll(pMgr):
    results =  pMgr.retrieve_all("businessTypes.Post")
    for item in results:
        print item.title

def testUpdate(pMgr):
    id  = 2
    result = pMgr.load_by_key("businessTypes.Post", id)
    result[0].body = "The body of post # %d has been updated." % id
    result[0].modified = datetime.now()

    pMgr.update(result)


def testCustomDelete(pMgr, objectTypeName, targetID):
    
    targetTable =  pMgr.typeMap[objectTypeName]

    u = targetTable.update(targetTable.c.id==targetID)
    u.execute(deleted=True)
   
    pMgr.database.getSession().flush()




def testPlugin(pMgr):
    plugin = SamplePlugin()
    pMgr.registerPlugin(plugin, "test")
    post = Post()
    return pMgr.callPlugin("test", post)



def testDelete():
    pass


def testMetadata(pMgr):
     users = pMgr.getTable('businessTypes.Person')
     query = users.select()
     cursor = query.execute()
     #rows = cursor.fetchall()

     print type(cursor)
     #print dir(cursor._metadata)
     #print cursor._metadata.keys
     
     

    



def main():

    pmgr = testConnect()
    #pmgr.mapTypeToTable('businessTypes.Person', 'persons')
    pmgr.mapParentToChild('businessTypes.Person', 'persons', 'person', 'businessTypes.ContactLog', 'contact_logs', 'contactLogs')


    #testInsert(pmgr)
    #testUpdate(pmgr)
    #testRetrieveAll(pmgr)    
    #testDelete(pmgr)

    #fieldMap = { 'id': 'ID', 'first_name': 'First Name', 'last_name': 'Last Name', 'address1':'Address'}
    #testReporting(pmgr, 'businessTypes.Person', fieldMap)

    #testMetadata(pmgr)

    
    

    reportGen = ExcelReportGenerator()

    env = Environment()
    env.bootstrap()


    
    cLogs = pmgr.getTable('businessTypes.ContactLog')

    startDate = date(2011, 5, 1)
    endDate = date(2011, 5, 27)

    query = cLogs.select(and_(cLogs.c.contact_date >= startDate, cLogs.c.contact_date <= endDate))

    fieldMap = {}
    workbook = reportGen.createSpreadsheet(query.execute(), fieldMap)
    workbook.save('test_spreadsheet.xls')
    
    
    
    #result = pmgr.load_by_key("businessTypes.Post", 2)
    #print result[0].body

   # print testPlugin(pmgr)

    #testCustomDelete(pmgr, "businessTypes.Post", 2)
    
   
if __name__ == '__main__':
    main()


