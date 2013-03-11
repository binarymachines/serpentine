
from sutility import *
from sqlalchemy import *
from bottle import redirect
import time, datetime
import random
import md5
import re
import logging


# Constants representing the allowed types in the Serpentine security paradigm
#

class ObjectType:
    FRAME = 'frame'
    METHOD = 'method'
    EVENT = 'event'

    
class TrusteeType:
    USER = 'user'
    GROUP = 'group'
    
    
class ActionType:
    RENDER = 'render'
    CALL = 'call'
    TRIGGER = 'trigger'

    
class SecurityPosture:
    OPEN = 'open'
    CLOSED = 'closed'

class SecurityEventType:
    AUTHENTICATION = 'authentication'
    AUTHORIZATION = 'authorization'
    LOGIN ='login'
    LOGOUT = 'logout'
    
class ACLEntryType:
    ALLOW = 'Allow'
    DENY = 'Deny'


class AuthStatusErrorType:
    NONE = 'not found'
    EXPIRED = 'expired'



class SecurityException(Exception):
    def __init__(self, securityEventType, message):
        errorMessage = 'Error attempting %s: %s' % (securityEventType, message)
        Exception.__init__(self, errorMessage)


class SecurityLoggingAgent:
    def __init__(self, eventTypesArray = [SecurityEventType.AUTHENTICATION,
                                          SecurityEventType.AUTHORIZATION,
                                          SecurityEventType.LOGIN,
                                          SecurityEventType.LOGOUT]):
        self.loggedEventTypes = {}
        for type in eventTypesArray:
            self.loggedEventTypes[type] = True
        self.displayStackTraceForExceptions = False
        

    def logEvent(self, eventType, message, exception = None):
        if not self.loggedEventTypes.get(eventType):
            return

        timestamp = str(datetime.datetime.now())
        if not exception:
            logEntry = '* Security log: %s event recorded at %s: %s' % (eventType, timestamp, message)
            logger.info(logEntry)
        else:
            logEntry = '* Security log: %s recorded during %s event at %s: %s' % (exception.__class__.__name__, eventType, timestamp, message)
            logger.error(logEntry)
        

    def showExceptionStackTrace(self):
        self.displayStackTraceForExceptions = True


    def hideExceptionStackTrace(self):
        self.displayStackTraceForExceptions = False



class AuthToken:
    def __init__(self, sessionID, userID, groupIDArray):
        self.sessionID = sessionID
        self.userID = userID
        self.groupMemberships = {}
        for groupID in groupIDArray:
            self.groupMemberships[groupID] = True

        # timestamp is in seconds; Serpentine security measures token time-to-live
        # in seconds as well
        self.timestamp = time.mktime(time.gmtime())  
        self.data = {}
        self.timeToLive = 0
        
        
    def setValue(self, name, value):
        self.data[name] = value

        
    def getValue(self, name):
        return self.data.get(name, '')


    def isOwnedBy(self, userID):
        if self.userID == userID:
            return True
        return False


    def isOwnedByMemberOf(self, groupID):
        return self.groupMemberships.get(groupID, False)


    def age(self):
        currentTime = time.mktime(time.gmtime())
        return currentTime - self.timestamp
        
    def isExpired(self):
        return self.age() > self.timeToLive
        
        
    def __repr__(self):
        return 'Serpentine authtoken [session ID: %s | owner: %s | timestamp: %d | age: %d seconds]' % (self.sessionID, self.userID, self.timestamp, self.age())



class ACLEntry:
    def __init__(self, trusteeID, trusteeType, actionType, accessAllowedFlag):
        self.trusteeID = trusteeID
        self.trusteeType = trusteeType  # (USER | GROUP)
        self.actionType = actionType  # valid action types depend on the type of object which owns this entry's enclosing ACL
        self.accessAllowed = accessAllowedFlag

    def __repr__(self):
        if self.accessAllowed:
            accessString = 'granted'
        else:
            accessString = 'denied'
            
        return '>>> ACL Entry. %s with ID "%s" is %s permission to %s the secured object.' % \
            (self.trusteeType, self.trusteeID, accessString, self.actionType)


class AccessAllowedACLEntry(ACLEntry):
    def __init__(self, trusteeID, trusteeType, actionType):
        ACLEntry.__init__(self, trusteeID, trusteeType, actionType, True)


class AccessDeniedACLEntry(ACLEntry):
    def __init__(self, trusteeID, trusteeType, actionType):
        ACLEntry.__init__(self, trusteeID, trusteeType, actionType, False)




class AccessControlList:
    def __init__(self):
        self.entries = { ACLEntryType.DENY:[], ACLEntryType.ALLOW:[]  }

        
    def addEntry(self, aclEntry):
        if aclEntry.accessAllowed:
            self.entries[ACLEntryType.ALLOW].append(aclEntry)
        else:
            self.entries[ACLEntryType.DENY].append(aclEntry)

        
    def clearAllEntries(self):
        self.entries.clear()


    def _accessIsExplicitlyDenied(self, authToken, actionType):
        """Walk the ACL to determine whether the owner of the passed AuthToken has been
        specifically forbidden from performing the specified action, returning True if so,
        False otherwise.
        """

        result = False
        for entry in self.entries[ACLEntryType.DENY]:
            if entry.actionType == actionType and entry.trusteeType == TrusteeType.USER:
                if authToken.userID == entry.trusteeID:
                    result = True
            elif entry.actionType == actionType and entry.trusteeType == TrusteeType.GROUP:
                if authToken.isOwnedByMemberOf(entry.trusteeID):
                    result = True

        return result

    
    def _accessIsExplicitlyAllowed(self, authToken, actionType):
        """Walk the ACL to determine whether the owner of the passed AuthToken has been
        specifically allowed to perform the specified action, returning True if so,
        False otherwise.
        """

        result = False
        for entry in self.entries[ACLEntryType.ALLOW]:
            if entry.actionType == actionType and entry.trusteeType == TrusteeType.USER:
                if authToken.userID == entry.trusteeID:
                    result = True
            elif entry.actionType == actionType and entry.trusteeType == TrusteeType.GROUP:
                if authToken.isOwnedByMemberOf(entry.trusteeID):
                    result = True
            
        return result


    def __repr__(self):
        aclContents = ''
        for entry in self.entries[ACLEntryType.ALLOW]:
            aclContents += '%s\n' % str(entry)
            
        for entry in self.entries[ACLEntryType.DENY]:
            aclContents += '%s\n' % str(entry)
            
        result = 'Access Control List:\n%s' % aclContents
        return result



    def shouldAllowAccess(self, authToken, actionType, securityPosture):
        
        if securityPosture == SecurityPosture.CLOSED:
            # In a closed posture, access is denied by default,
            # so no need to check for explicit denials; short-circuit
            if not self._accessIsExplicitlyAllowed(authToken, actionType):
                return False
            else:
                return True

        elif securityPosture == SecurityPosture.OPEN:
            # In an open posture, access is granted by default, 
            # so no need to check for explicit allowances; short-circuit
            if not self._accessIsExplicitlyDenied(authToken, actionType):
                return True
            else:
                return False
                            


class Restriction:
    def __init__(self, accessControlList, denialRedirectRoute):
        self.acl = accessControlList
        self.redirectRoute = denialRedirectRoute
        


class UserAuthenticator:
    def __init__(self, 
                 loginUserIDFieldName = 'username',
                 loginPasswordFieldName = 'password'):
        self.loginUserIDFieldName = loginUserIDFieldName
        self.loginPasswordFieldName = loginPasswordFieldName


    def _authenticate(self, userName, password, sessionID, loggingAgent, **kwargs):
        """Perform the actual user authentication
           and return a valid AuthToken object. Override in child class."""        
        return None
    

    def authenticateUser(self, httpRequest, loggingAgent, **kwargs):
        """Return a newly-created auth token for the user credentials,
        embedded in the httpRequest, if valid. If not, return None """
        
        httpSession = httpRequest.environ['beaker.session']
        sessionID = httpSession.id
        userName = httpRequest.POST.get(self.loginUserIDFieldName)
        password = httpRequest.POST.get(self.loginPasswordFieldName)    
        return self._authenticate(userName, password, sessionID, loggingAgent)



class SQLUserAuthenticator(UserAuthenticator):

    def __init__(self, persistenceManager):
        UserAuthenticator.__init__(self)
        self.persistenceManager = persistenceManager
        
        
    def _authenticate(self, userName, password, sessionID, loggingAgent, **kwargs):
        userTable = self.persistenceManager.loadTable('users')

        try:
            dbSession = self.persistenceManager.getSession()
            # TODO: modify query to be aware of group memberships
            userAuthQuery = dbSession.query(userTable).filter(and_(userTable.c.username == userName, userTable.c.password == password))
            result = userAuthQuery.all()
            if result:
                return AuthToken(sessionID, userName, [])
            else: 
                loggingAgent.logEvent(SecurityEventType.AUTHENTICATION, 'incorrect username or password.')
                return None
        except SQLAlchemyException, err:
            loggingAgent.logAuthenticationEvent(SecurityEventType.AUTHENTICATION, 'database error', err)
            return None
        finally:
            dbSession.close()
        
        
  

class IDGenerator:
    def __init__(self):
        pass

    def generateUniqueID(self, tag=''):
        """Build a new Session ID"""
        t1 = time.time()
        time.sleep(random.random())
        t2 = time.time()
        base = md5.new(tag + str(t1 + t2))
        if tag:
            newID = '%s_%s' % (tag, base.hexdigest())
        else:
            newID = base.hexdigest()
        return newID 


class ValidationStatus:
    def __init__(self, isOK, redirectRoute=None):
        self.ok = isOK
        self.message = ''
        self.redirectRoute = None
        if not self.ok:
            self.redirectRoute = redirectRoute

            
class AuthStatus:
    def __init__(self, isOK, token, message=''):
        self.ok = isOK
        self.token = token
        self.message = message



class AuthStatusOK(AuthStatus):
    def __init__(self, token):
        AuthStatus.__init__(self, True, token)



class AuthStatusError(AuthStatus):
    def __init__(self, message):
        AuthStatus.__init__(self, False, None, message)



class SecurityManager:
    def __init__(self,                 
                 userAuthenticator,
                 idGenerator,
                 authTokenLifespanSeconds,
                 loggingAgent,
                 userLoginRedirectRoute = 'login'):

        self.userAuthenticator = userAuthenticator
        self.idDGenerator = idGenerator
        self.securedObjects = {}
        self.allowedLogins = {}
        self.authTokenLifespanSeconds = authTokenLifespanSeconds
        self.loggingAgent = loggingAgent
        self.loginRedirectRoute = userLoginRedirectRoute
        self.sessionToTokenMap = {}
    

        
    def configureObjectAccess(self, objectID, objectType, permissionsArray):
        """Parse an array of YAML configuration fragments in the form:
        
        - action: render
          access: allow(user1, &group1), deny(user2), allow(&group3)
          
        and allow/deny access to the target object accordingly."""
          
        
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
                trusteeListString = string.strip('allow').strip('(').rstrip(')')
                trusteeArray = [t.strip() for t in trusteeListString.split(',')]
                
                for name in trusteeArray:
                    if name.startswith('&'):
                        groupID = name.strip('&')
                        self.permitGroupAccess(groupID, objectID, objectType, action)                        
                    else:
                        self.permitUserAccess(name, objectID, objectType, action)
                
            for string in denyStrings:   
                print '### Permission denial string found: %s (on %s ID %s)' % (string, objectType, objectID)
                trusteeListString = string.strip('deny').strip('(').rstrip(')')
                trusteeArray = [t.strip() for t in trusteeListString.split(',')]

                for name in trusteeArray:
                    
                    if name.startswith('&'):
                        groupID = name.strip('&')
                        self.denyGroupAccess(groupID, objectID, objectType, action)               
                    else:
                        self.denyUserAccess(name, objectID, objectType, action)


       
    def secureObject(self, objectID, objectType, denialRedirectRoute):

        # If an object does not have an access control list associated with it
        # (in other words, if we have not invoke secureObject() with the object in question as a target)
        # Serpentine will grant access to it, provided the default application 
        # security posture is OPEN. If it is CLOSED, Serpentine will deny access.
        self.securedObjects[(objectID, objectType)] = Restriction(AccessControlList(), denialRedirectRoute)


    def objectIsSecured(self, objectID, objectType):
        return (objectID, objectType) in self.securedObjects


    def permitUserAccess(self, userID, objectID, objectType, actionType):
        if (objectID, objectType) not in self.securedObjects:
            raise NoSuchRestrictionError(objectID, objectType)
        restriction = self.securedObjects[(objectID, objectType)]
        restriction.acl.addEntry(AccessAllowedACLEntry(userID, TrusteeType.USER, actionType))


    def denyUserAccess(self, userID, objectID, objectType, actionType):
        if (objectID, objectType) not in self.securedObjects:
            raise NoSuchSecuredObjectError(objectID, objectType)
        restriction = self.securedObjects[(objectID, objectType)]
        restriction.acl.addEntry(AccessDeniedACLEntry(userID, TrusteeType.USER, actionType))


    def permitGroupAccess(self, groupID, objectID, objectType, actionType):
        if (objectID, objectType) not in self.securedObjects:
            raise NoSuchSecuredObjectError(objectID, objectType)
        restriction = self.securedObjects[(objectID, objectType)]
        restriction.acl.addEntry(AccessAllowedACLEntry(groupID, TrusteeType.GROUP, actionType))


    def denyGroupAccess(self, groupID, objectID, objectType, actionType):
        if (objectID, objectType) not in self.securedObjects:
            raise NoSuchSecuredObjectError(objectID, objectType)
        restriction = self.securedObjects[(objectID, objectType)]
        restriction.acl.addEntry(AccessDeniedACLEntry(groupID, TrusteeType.GROUP, actionType))


    def validateObjectRequest(self, authToken, objectID, objectType, actionType, securityPosture):
        if (objectID, objectType) not in self.securedObjects:
            return ValidationStatus(True)

        restriction = self.securedObjects[(objectID, objectType)]
        acl = restriction.acl
        result = acl.shouldAllowAccess(authToken, actionType, securityPosture)

        if not result:
            return ValidationStatus(result, restriction.redirectRoute)
            
        return ValidationStatus(result)


    def getAuthToken(self, httpRequest, environment):        

        # if the application's default security posture is OPEN,
        # Serpentine will only call authenticateUser() in response to an atttempt
        # to access a secured object (see secureObject(...) method). If the default posture
        # is CLOSED, Serpentine will call authenticateUser() for every route.
        #

        authToken = None

        # get the HTTP session information
        httpSession = httpRequest.environ['beaker.session']
        sessionID = httpSession.id
        
        authToken = self.sessionToTokenMap.get(sessionID)
        if not authToken:
            #  no authtoken has been created for this user; needs to login
            return None
        elif authToken.isExpired():
            # do not accept tokens older than the time-to-live
            # (and while we're at it, remove them)
            self.loggingAgent.logEvent(SecurityEventType.AUTHORIZATION,
                                       'Found expired authtoken for user %s. Clearing token.' % authToken.userID)            
            self.sessionToTokenMap.pop(sessionID)          
            return None
        elif authToken.sessionID != sessionID:
            self.loggingAgent.logEvent(SecurityEventType.AUTHORIZATION,
                                       'ALERT: Authtoken for user %s has a non-matching session ID.' % authToken.userID)
            self.loggingAgent.logEvent(SecurityEventType.AUTHORIZATION,
                                       'ALERT: This token may have been altered by a hostile actor. Clearing token.' % authToken.userID)
            
            self.sessionToTokenMap.pop(sessionID)
            return None
            
        self.loggingAgent.logEvent(SecurityEventType.AUTHORIZATION, 'Found valid authtoken for user %s.' % authToken.userID)
        return authToken

    
    def clearAuthToken(self, httpRequest):            
        httpSession = httpRequest.environ['beaker.session']
        sessionID = httpSession.id
        if sessionID in self.sessionToTokenMap:        
            self.sessionToTokenMap.pop(sessionID)


    def login(self, httpRequest):

        # This function is only invoked from the main application's /login route via HTTP POST
        # when the user fills out a login form.
        httpSession = httpRequest.environ['beaker.session']
        sessionID = httpSession.id
        
        authToken = self.userAuthenticator.authenticateUser(httpRequest, self.loggingAgent)
        if not authToken:
            raise SecurityException(SecurityEventType.LOGIN, 'Invalid username or password.')
        
        authToken.timeToLive = self.authTokenLifespanSeconds
        self.sessionToTokenMap[sessionID] = authToken
        return authToken
        


    def logout(self, httpRequest, environment):
        pass
  
  
    
    def dumpPermissions(self):
        for key in self.securedObjects:            
            print '[ Secured object ID %s (type: %s) ]' % (key[0], key[1])
            restriction = self.securedObjects[key]
            print restriction.acl
            print '(denied users will be redirected to %s.)\n' % restriction.redirectRoute
        
        print 'Done.'
        
            
        
        
        




