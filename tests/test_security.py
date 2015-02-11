from db import *
from security import *
from environment import *

import re
import yaml


def testAuthenticator():
    mydb = MySQLDatabase('localhost', 'bifrost')
    mydb.login('dtaylor', 'notobvious')
    pMgr = PersistenceManager(mydb)
    sqla = SQLUserAuthenticator(pMgr)

    token = sqla._authenticate('johndoe', 'notobvious', 'sessionabc1', None)
    print 'User johndoe authenticated.'
    print token

    token2 = sqla._authenticate('janedoe', 'wrongpassword', 'sessiondef2', None)
    if token2:
        print 'ERROR: should not have authenticated user.'
    else:
        print 'User janedoe not authenticated: incorrect password.'



def testACL():
    mydb = MySQLDatabase('localhost', 'bifrost')
    mydb.login('dtaylor', 'notobvious')
    pMgr = PersistenceManager(mydb)
    sqla = SQLUserAuthenticator(pMgr)

    token = sqla._authenticate('johndoe', 'notobvious', 'sessionabc1', None)
    print 'User johndoe authenticated.'

    acl = AccessControlList()

    # explicitly deny access to user johndoe
    acl.addEntry(AccessDeniedACLEntry('johndoe', TrusteeType.USER, ActionType.RENDER))
    print 'Is johndoe allowed access? %s' % acl.shouldAllowAccess(token, ActionType.RENDER, SecurityPosture.CLOSED)



def testLoggingAgent():
    agent = SecurityLoggingAgent()
    agent.logEvent(SecurityEventType.AUTHENTICATION, 'user johndoe logged in.')
    agent.logEvent(SecurityEventType.AUTHORIZATION, 'user janedoe did a bad thing', Exception('Foobar error raised'))
    



def parsePermissionsArray(permissionsArray, objectType, objectGroup):
    """Parse an array of YAML configuration fragment in the form:
    
    - action: render
      access: allow(user1, &group1), deny(user2), allow(&group3)
      
    and return an array of Permission objects."""
      
    accessStringRX = re.compile(r'')
    accessAllowedRX = re.compile(r'allow\([a-zA-Z0-9&\,\s]+\)')
    accessDeniedRX = re.compile(r'deny\([a-zA-Z0-9&\,\s]+\)')
    
    permissions = []
    for element in permissionsArray:
        action = element['action']
        accessString = element['access']
        
        allowStrings = accessAllowedRX.findall(accessString)
        denyStrings = accessDeniedRX.findall(accessString)
        
        # allowStrings and denyStrings are arrays where each element
        # is the string 'allow' or 'deny' followed 
        # by a comma-separated list of trustees, enclosed
        # by parentheses. For example: 'allow(user1, &group1)'
        #
        for string in allowStrings: 
            startIndex = string.find('(')+1
            endIndex = len(string)-1
            trusteeListString = string[startIndex:endIndex]
            trusteeArray = [t.strip() for t in trusteeListString.split(',')]
            print 'Entities granted permission to %s any %s in object group "%s": %s\n' % (action, objectType, objectGroup, trusteeArray)
            
            for name in trusteeArray:
                if name.startswith('&'):
                    targetACL.addEntry(AccessAllowedACLEntry(name, TrusteeType.GROUP, ActionType.RENDER))
                else:
                    targetACL.addEntry(AccessAllowedACLEntry(name, TrusteeType.USER, ActionType.RENDER))
            
        for string in denyStrings:
            startIndex = string.find('(')+1
            endIndex = len(string)-1
            trusteeListString = string[startIndex:endIndex]
            trusteeArray = [t.strip() for t in trusteeListString.split(',')]
            print 'Entities denied permission to %s any %s in object group "%s": %s\n' % (action, objectType, objectGroup, trusteeArray)
            
            processUserPermissions()
            
            for trusteeID in trusteeArray:
                if name.startswith('&'):
                    targetACL.addEntry(AccessDeniedACLEntry(name, TrusteeType.GROUP, ActionType.RENDER))                
                else:
                    securityManager.permitUserAccess(trusteeID, objectID, objectType, actionType)
                    targetACL.addEntry(AccessDeniedACLEntry(name, TrusteeType.USER, ActionType.RENDER))
                
                
def testSecurityConfigParsing():

    environment = Environment()
    environment.bootstrap('bifrost.conf')
    
    environment.populateContentRegistry()
    environment.assignControllers()
    environment.mapFramesToViews()
    environment.assignStylesheetsToXMLFrames()
    environment.initializeDataStore()
    
    environment.initializeEventDispatcher()
    environment.mapModelsToDatabase()
    environment.loadResponders()
    environment.loadDatasources()
   
    environment.loadControls()
    environment.dispatcher = EventDispatcher()
    environment.initializeReporting()
    
    environment.initializeSecurity()
    
    environment.securityManager.dumpPermissions()
    
    """"
    print environment._findObjectAliases('(*.index)', ObjectType.METHOD)
    print environment._findObjectAliases('Distributor.*', ObjectType.METHOD)
    print environment._findObjectAliases('*', ObjectType.FRAME)
    """
    
    
    

    """"
    f = open('bifrost.conf')
    config = yaml.load(f.read())
    
    registry = config.get('security_registry')
    
    securedObjectGroups = registry['secured_object_groups']
    
    for objectGroup in securedObjectGroups:
        objectType = securedObjectGroups[objectGroup]['object_type']
        memberListString = securedObjectGroups[objectGroup]['members']
        
        permissions = securedObjectGroups[objectGroup]['permissions']
        
        print 'Found %s group ID %s. Members: %s.' % (objectType, objectGroup, memberListString)
        parsePermissionsArray(permissions, objectType, objectGroup)
    """

if __name__ == '__main__':
    #testAuthenticator()
    #testACL()
    #testLoggingAgent()
    testSecurityConfigParsing()
