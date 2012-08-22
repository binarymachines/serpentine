#!/usr/bin/env python

#------ Database module --------

from sqlalchemy import *
from sqlalchemy.orm import mapper, scoped_session, sessionmaker, relation, clear_mappers
from wtforms import Form

import types
import os
import exceptions
import sys



from core import *


class NoSuchTableError(Exception):
    def __init__(self, tableName, schemaName):
        Exception.__init__(self, "No table named '%s' exists in database schema '%s'." % (tableName, schemaName))


Session = scoped_session(sessionmaker(autoflush=False, autocommit=False, expire_on_commit=False))

class Database:
    """A wrapper around the basic SQLAlchemy DB connect logic.

    """

    def __init__(self, dbType, host, schema):
        """Create a Database instance ready for user login.

        Arguments:
        dbType -- for now, 'mysql' only
        host -- host name or IP
        schema -- the database schema housing the desired tables
        """

        self.dbType = dbType
        self.host = host
        self.schema = schema
        self.engine = None
        self.metadata = None
        
        

    def __createURL__(self, dbType, username, password):
        """Implement in subclasses to provide database-type-specific URL formats."""

        pass

    def login(self, username, password):    
        """Connect as the specified user."""

        url = self.__createURL__(self.dbType, username, password)
        self.engine = create_engine(url)
        self.metadata = MetaData(self.engine)
        self.metadata.reflect(bind=self.engine)
        
        #self.sessionFactory.configure(bind=self.engine)
        Session.configure(bind=self.engine)
        
        

    def getMetaData(self):
        return self.metadata

    def getEngine(self):
        return self.engine

    def getSession(self):        
        #return self.Session()
        return Session()

    def listTables(self):
        return self.metadata.tables.keys()

    def getTable(self, name):
        """Passthrough call to SQLAlchemy reflection logic. 

        Arguments:
        name -- The name of the table to retrieve. Must exist in the current schema.

        Returns: 
        The requested table as an SQLAlchemy Table object.
        """

        if name not in self.metadata.tables:
            raise NoSuchTableError(name, self.schema)

        return self.metadata.tables[name]



class MySQLDatabase(Database):
    """A Database type for connecting to MySQL instances."""

    def __init__(self, host, schema):
        Database.__init__(self, "mysql", host, schema)
        
    def __createURL__(self, dbType, username, password):
        return "%s://%s:%s@%s/%s" % (self.dbType, username, password, self.host, self.schema)


class NoSuchPluginError(Exception):
    def __init__(self, pluginName):
        Exception.__init__(self, "No plugin registered under the name '%s'." % pluginName)


class PluginMethodError(Exception):
    def __init__(self, pluginName, pluginMethodName):
        Exception.__init__(self, "The plugin registered as '%s' does not contain an execute() method." % (pluginName))


class PersistenceManager:
    """A logic center for database operations in a Serpentine app. 

    Wraps SQLAlchemy lookup, insert/update, general querying, and O/R mapping facilities."""
    
    def __init__(self, database):
        self._typeMap = {}
        self.modelAliasMap = {}
        self.database = database
        self.metaData = database.getMetaData()
        self.pluginTable = {}
        self.mappers = {}


    def __del__(self):
        clear_mappers()

    def getSession(self):
        return self.database.getSession()

    def loadTable(self, tableName):
        """Retrieve table data using SQLAlchemy reflection"""

        return Table(tableName, self.metaData, autoload = True)

    def str_to_class(self, objectTypeName):
        """A rudimentary class loader function.

        Arguments: 
        objectTypeName -- a fully qualified name for the class to be loaded,
        in the form 'packagename.classname'. 

        Returns:
        a Python Class object.
        """

        if objectTypeName.count('.') == 0:
            moduleName = __name__
            typeName = objectTypeName
        else:
            tokens = objectTypeName.rsplit('.', 1)
            moduleName = tokens[0]
            typeName = tokens[1]

        try:
            identifier = getattr(sys.modules[moduleName], typeName)
        except AttributeError:
            raise NameError("Class %s doesn't exist." % objectTypeName)
        if isinstance(identifier, (types.ClassType, types.TypeType)):
            return identifier
        raise TypeError("%s is not a class." % objectTypeName)

    def query(self, objectType, session):
        """A convenience function to create an SQLAlchemy Query object on the passed DB session.

        Arguments:
        objectType -- a Python class object, most likely returned from a call to str_to_class(...)

        Returns:
        An SQLAlchemy Query object, ready for data retrieval or further filtering. See SQLAlchemy docs
        for more information on Query objects.
        """

        return session.query(objectType)


    def mapTypeToTable(self, modelClassName, tableName, **kwargs):
        """Call-through to SQLAlchemy O/R mapping routine. Creates an SQLAlchemy mapper instance.

        Arguments:
        modelClassName -- a fully-qualified class name (packagename.classname)
        tableName -- the name of the database table to be mapped to this class
        
        """

        dbTable = Table(tableName, self.metaData, autoload=True)        
        objectType = self.str_to_class(modelClassName)     
        if objectType not in self.mappers:
            self.mappers[objectType] = mapper(objectType, dbTable)

        if 'model_alias' in kwargs:
            modelAlias = kwargs['model_alias']
        else:
            modelAlias = modelClassName

        self.modelAliasMap[modelAlias] = modelClassName
        self._typeMap[modelClassName] = dbTable
        
    
    def mapParentToChild(self, parentTypeName, parentTableName, parentTypeRefName, childTypeName, childTableName, childTypeRefName, **kwargs):
        """Create a parent-child (one to many relationship between two DB-mapped entities in SQLAlchemy's O/R mapping layer.

        Arguments:

        Returns:
        """
    
        parentTable = Table(parentTableName, self.metaData, autoload=True)
        parentObjectType = self.str_to_class(parentTypeName)

        childTable = Table(childTableName, self.metaData, autoload=True)
        childObjectType = self.str_to_class(childTypeName)

        if childObjectType not in self.mappers:
            self.mappers[childObjectType] = mapper(childObjectType, childTable)

        self.mappers[parentObjectType] = mapper(parentObjectType, parentTable, properties={
                childTypeRefName : relation(childObjectType, backref = parentTypeRefName)})

        parentAlias = kwargs['parent_model_alias']
        childAlias = kwargs['child_model_alias']

        self.mapTypeToTable(parentTypeName, parentTable.name, model_alias = parentAlias)
        self.mapTypeToTable(childTypeName, childTable.name, model_alias = childAlias)
        

        
    def mapPeerToPeer(self, parentTypeName, parentTableName, parentTypeRefName, peerTypeName, peerTableName, peerTypeRefName, **kwargs):
        """Create a peer-peer (one to one) relationship between two DB-mapped entities in SQLAlchemy's O/R mapping layer.

        Arguments:

        Returns:
        """

        parentTable = Table(parentTableName, self.metaData, autoload=True)
        parentObjectType = self.str_to_class(parentTypeName)

        peerTable = Table(peerTableName, self.metaData, autoload=True)
        peerObjectType = self.str_to_class(peerTypeName)

        if peerObjectType not in self.mappers:
            self.mappers[peerObjectType] = mapper(peerObjectType, peerTable, non_primary=True)

        self.mappers[parentObjectType] = mapper(parentObjectType, parentTable, properties={
                peerTypeRefName : relation(peerObjectType, backref = parentTypeRefName, uselist = False), })

        parentAlias = kwargs['model_alias']
        peerAlias = kwargs['peer_model_alias']

        self.mapTypeToTable(parentTypeName, parentTable.name, model_alias = parentAlias)
        self.mapTypeToTable(peerTypeName, peerTable.name, model_alias = peerAlias)
       


    def getTableForType(self, modelName):
        if modelName not in self.modelAliasMap:
            raise NoTypeMappingError(modelName)
        
        return self._typeMap[self.modelAliasMap[modelName]]

    def retrieveAll(self, objectTypeName, session):
        objClass = self.str_to_class(objectTypeName)
        resultSet = session.query(objClass).all()
        return resultSet
    
    def insert(self, object, session):
        session.add(object)

    def update(self, object, session):
        session.flush()
        
    def delete(self, object, session):
        session.delete(object)

    def loadByKey(self, objectTypeName, objectID, session):
        query = session.query(self.str_to_class(objectTypeName)).filter_by(id = objectID)
        return query.first()

    def registerPlugin(self, plugin, name):
        self.pluginTable[name] = plugin

    def callPlugin(self, pluginName, targetObject):
        plugin = self.pluginTable[pluginName]
        if plugin == None:
            raise NoSuchPluginError(pluginName)
    
        try:
            return plugin.performOperation(self, targetObject)
        except AttributeError as err:
            raise PluginMethodError(pluginName, 'execute')

    
class PersistenceManagerPlugin:
    def __init__(self):
        pass
        
    def performOperation(self, persistenceMgr, object):
        method = getattr(self, 'execute')
        
        return method(persistenceMgr, object)

    def __execute__(persistenceMgr, object):  # override in subclasses
        pass





           

# a repository for WTForms 

class FormClassRegistry:
    def __init__(self):
        self.operationMap = {}
        self.typeMap = {}
        self.formMap = {}

    def addFormClass(self, opType, objectType, formClassName):  # classname must be fully-qualified; class must extend WTForms "Form"
        if self.formMap.has_key(objectType):
            self.formMap[objectType][opType] = formClassName
        else:
            opDict = { opType:formClassName }
            self.formMap[objectType] = opDict

    def getFormClass(self, opType, objectType):
        try:
           formClassName = self.formMap[objectType][opType]
           paths = formClassName.split('.')
           moduleName = '.'.join(paths[:-1])
           className = paths[-1]
   
           return getattr(__import__(moduleName), className)

        except KeyError:
            raise FormConfigError("No form class has been registered for operation '%s' on type '%s'." % (opType, objectType))

    
class FormStatus:
    def __init__(self, isOK, message = None, exception = None):
        self.isOK = isOK
        self.message = message
        self.exception = exception

    def __repr__(self):
        return "FormStatus isok=%s. Message: %s, exception: %s" % (self.isOK, self.message, self.exception) 
       


# form operations: create | update | delete | select
# db operations: form ops, plus: load_by_key | retrieve_all
        
class FormHandler:
    def __init__(self, formRegistry, persistenceManager):
        self.formRegistry = formRegistry
        self.pMgr = persistenceManager
        self.funcTable = {}
        self.funcTable['create'] = self.create
        #self.funcTable['update'] = self.update
        #self.funcTable['delete'] = self.delete
        #self.funcTable['select'] = self.select

    def acceptPost(self, objectType, operationType, httpRequest):
        try:
            formClass = self.formRegistry.getFormClass(operationType, objectType)
            if operationType in self.funcTable.keys:
                return self.funcTable[operationType](objectType, operationType, httpRequest)
            else:
                return FormStatus(False, "Form operation '%s' is not a recognized operation." % operationType)
        except FormHandlerError as err:
            status = FormStatus(False, "Error handling %s operation" % operationType, err)


    def acceptGet(self, objectType, operationType, httpRequest):
        try:
            formClass = self.formRegistry.getFormClass(operationType, objectType)
            if operationType in self.funcTable:
                return self.funcTable[operationType](objectType, operationType, httpRequest)
            else:
                raise FormHandlerError("Form operation '%s' is not a recognized operation." % operationType)
        except FormHandlerError as err:
            status = FormStatus(False, "Error handling %s operation" % operationType, err)


    def create(self, objectType, operation, request):
        session=request.environ["beaker.session"]
        session["counter"] += 1
        counter = session["counter"]
        newPost = businessTypes.Post()
        newPost.firstName = "John"
        newPost.lastName = "Doe"
        newPost.status = "okay by me"

        session["current_post"] = newPost
        session.save()
        status = FormStatus(True, message="Handled create form, counter is now %s" % session["counter"])
        return status

"""
    def update(self, objectType, operationType, httpRequest):
        formClass = self.formRegistry.getFormClass(operationType, objectType)
        objectToUpdate  = httpRequest.selectedObject
        form = formClass(httpRequest.POST, objectToUpdate)
        if form.validate():
            objectToUpdate.save()
            return FormStatus('ok')
        else:
            return FormStatus('error', form)

    def delete():
        pass

"""
            


