import os
import exceptions
import sys
import logging

from bottle import redirect
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.exc import NoResultFound




# Core functionality module ------------

logging.basicConfig( filename = 'bifrost.log', level = logging.INFO, format = "%(asctime)s - %(message)s" )
log = logging.info


class MaxUploadSizeError(Exception):
    def __init__(self, maxSize):
        Exception.__init__(self, 'Uploaded file must be less than %d bytes.' % maxSize)

class InvalidPageNumberError(Exception):
    def __init__(self, pageNumber):
        Exception.__init__(self, "Pagination cannot use a negative or zero page number.")

class NoControllerMethodError(Exception):
    def __init__(self, controllerMethod, objectType):
        Exception.__init__(self, "Controller method '%s' for object type '%s' \
                           either does not exist or is not callable." \
                           % (controllerMethod, objectType))

class NoSuchControllerError(Exception):
  def __init__(self, objectType):
    Exception.__init__(self,
                       "No Controller object has been assigned to the type %s" % objectType)

class ClassLoaderError(Exception):
    def __init__(self, fqClassName):
        Exception.__init__(self,
                           "Cannot find Python class with fully-qualified name '%s'. \
                           Please check your modules and PYTHONPATH." % fqClassName)

class ConfigError(Exception):
      def __init__(self, message):
            Exception.__init__(self, message)

class ObjectLookupError(Exception):
    def __init__(self, objectType, objectID):
        Exception.__init__(self,
                           "No object of type %s with ID %s found in database." \
                           % (objectType, str(objectID)))

class NoTypeMappingError(Exception):
    def __init__(self, className):
        Exception.__init__(self,
                           "No database table has been mapped to class %s." \
                           % className)

class FormHandlerError(Exception):
    def __init__(self, message):
        Exception.__init__(self, message)

class FormValidationError(Exception):
    def __init__(self, operation, objectType, errorDict):
        self.errors = errorDict
        Exception.__init__(self,
                           'Form validation for %s %s failed with errors \
                           in the following fields: %s.' \
                           % (objectType, operation, ','.join(errorDict.keys())))

class FormConfigError(Exception):
    def __init__(self, message):
        Exception.__init__(self, message)

class DatabaseError(Exception):
    def __init__(self, message):
        Exception.__init__(self, message)

class NoSuchFrameError(Exception):
    def __init__(self, frameID):
        Exception.__init__(self,
                           "No content frame registered under alias '%s'. " % frameID)

class NoSuchResponderError(Exception):
    def __init__(self, responderAlias):
        Exception.__init__(self,
                           "No responder registered under alias '%s'." % responderAlias)

class NoSuchFormError(Exception):
    def __init__(self, frameID):
        Exception.__init__(self,
                           "No data input form has been registered to the content frame with ID '%s'. " % frameID)

class NoSuchStylesheetError(Exception):
    def __init__(self, filename):
        Exception.__init__(self,
                           "XSL stylesheet file '%s' could not be found. Please check your path and permissions." % filename)

class RenderError(Exception):
    def __init__(self, message):
        Exception.__init__(self, message)

class NoSuchViewError(Exception):
    def __init__(self, objectType, controllerMethod):
        Exception.__init__(self,
                           "No content frame has been mapped to object type %s and controller method %s" \
                               % (objectType, controllerMethod))

class TemplateConfigError(Exception):
    def __init__(self, message):
        Exception.__init__(self, message)


class MissingRequestParamError(Exception):
    def __init__(self, paramName):
        Exception.__init__(self,
                           "The inbound HTTP request is missing the parameter '%s'." % paramName)

class Singleton(object):
  __instance = None # the one, true Singleton
  
  def __new__(classtype, *args, **kwargs):
    # Check to see if a __instance exists already for this class
    # Compare class types instead of just looking for None so
    # that subclasses will create their own __instance objects
    if classtype != type(classtype.__instance):
      classtype.__instance = object.__new__(classtype, *args, **kwargs)
    return classtype.__instance

  def __init__(self,name=None):
    self.name = name

  def display(self):
    print self.name,id(self),type(self)


class ControllerStatus:
    def __init__(self, ok = True, errMessage = None):
        self.isok = ok
        self.message = errMessage
        self.data = {}

    def __str__(self):
        return "Controller returned %s. Message: %s" % (self.isok, self.message) 


class FrontController(Singleton):
  
  def __init__(self):
    self.controllerMap = {}

  def validate(self, httpRequest):
    return ControllerStatus()

  def assignController(self, controller, modelName):
    self.controllerMap[modelName] = controller


  def getController(self, modelName):
    if modelName not in self.controllerMap:
      raise NoSuchControllerError(modelName)
    else: 
      return self.controllerMap[modelName]



class BaseController(object):
    def __init__(self, modelClass): 

        # The type of object we are managing
        self.modelClass = modelClass
        self.model = None
        self.collection = []
        # The name we use to retrieve a generic object ID from the session
        self.genericIDSessionTag = 'object_id' 
        # The name we use to retrieve a specific type ID from the session
        self.typeSpecificIDSessionTag = ''.join([self.modelClass.__name__.lower(), '_id'])
        self.sessionName = 'beaker.session'

    def lookup(self, objectID, persistenceManager):
        dbSession = persistenceManager.getSession()
        try:            
            object = dbSession.query(self.modelClass).filter(self.modelClass.id == objectID).one()            
            return object
        except SQLAlchemyError, err:
            dbSession.rollback()
            log('Object lookup failed with message: %s' % err.message)
            # TODO: scaffolding to track down lookup 
            raise err
                
        
    def assertObjectExists(self, modelName, objectID, persistenceManager):
        if self.lookup(objectID, persistenceManager) is None:
            raise ObjectLookupError(modelName, objectID)
        
    def _index(self, persistenceManager):
        dbSession = persistenceManager.getSession()
        try:            
            query =  dbSession.query(self.modelClass)  
            collection = query.all()        
            return collection
        except SQLAlchemyError, err:
            dbSession.rollback()
            log("%s %s failed with message: %s" % (self.modelClass, 'index', err.message))
            raise err

    def _indexPage(self, persistenceManager, pageNumber, pageSize):
        dbSession = persistenceManager.getSession()
        try:            
            offset = (pageNumber - 1) * pageSize
            query =  dbSession.query(self.modelClass).limit(pageSize).offset(offset)
            collection = query.all()        
            return collection
        except SQLAlchemyError, err:
            dbSession.rollback()
            log("%s %s failed with message: %s" % (self.modelClass, 'index', err.message))
            raise err

    def index(self, objectType, httpRequest, context, **kwargs):
        
        frameID = context.viewManager.getFrameID(objectType, 'index')
        frameObject = context.contentRegistry.getFrame(frameID)
        
        # this is so that the render() call to the underlying XMLFrame object can look up its stylesheet
        httpRequest.params['frame'] = frameID   
                    
        collection = self._index(context.persistenceManager)
        kwargs['resultset'] = collection # TODO: rethink the variable name

        # Invoke helper function if one has been registered
        helperFunction = context.contentRegistry.getHelperFunctionForFrame(frameID)
        if helperFunction is not None:
            extraData = helperFunction(httpRequest, context)
            kwargs.update(extraData)

        return frameObject.render(httpRequest, context, **kwargs)
        

    # TODO: fix security hole, ensure pageNumber is an integer and a reasonable value

    def indexPage(self, objectType, pageNumber, httpRequest, context, **kwargs):
        
        frameID = context.viewManager.getFrameID(objectType, 'index')
        frameObject = context.contentRegistry.getFrame(frameID)
        
        # this is so that the render() call to the underlying XMLFrame object can look up its stylesheet
        httpRequest.params['frame'] = frameID   
         
        #
        # TODO: for now we hardcode the page size, but eventually we'll get it from the context object,
        # which in turn will read it from the config file.
        #
        pageSize = 50 # this is the number of records we show on a page
        collection = self._indexPage(context.persistenceManager, pageNumber, pageSize) 
        kwargs['resultset'] = collection # TODO: rethink the variable name

        # Invoke helper function if one has been registered
        helperFunction = context.contentRegistry.getHelperFunctionForFrame(frameID)
        if helperFunction is not None:
            extraData = helperFunction(httpRequest, context)
            kwargs.update(extraData)

        return frameObject.render(httpRequest, context, **kwargs)

    def _insert(self, object, persistenceManager): 
        dbSession = persistenceManager.getSession()
        try:            
            persistenceManager.insert(object, dbSession) 
            dbSession.commit()
        except SQLAlchemyError, err:    
            dbSession.rollback()
            log("%s failed with message: %s" % ('insert', err.message))
            raise err
    
    def insert(self, objectType, httpRequest, context, **kwargs):
        
        session = httpRequest.environ[self.sessionName]
        frameID = context.viewManager.getFrameID(objectType, 'insert')    
        frameObject = context.contentRegistry.getFrame(frameID)
        inputFormClass = context.contentRegistry.getFormClass(frameID)
        inputForm = inputFormClass()
        inputForm.process(httpRequest.POST) 
           
        if not inputForm.validate():
            raise FormValidationError(objectType, 'insert', inputForm.errors)

        object = self.modelClass()
        inputForm.populate_obj(object)        
        self._insert(object, context.persistenceManager)
        
        snapback = httpRequest.POST.get('snapback', '').strip()
        if len(snapback):
            redirectTarget = '/%s/%s' % (context.urlBase, snapback)
        else:
            redirectTarget = '/%s/controller/%s/index' % (context.urlBase, objectType)

        redirect(redirectTarget)
                

    def _update(self, object, persistenceManager):
        dbSession = persistenceManager.getSession()
        try:
            persistenceManager.update(object, dbSession)  
            dbSession.commit()
        except SQLAlchemyError, err:
            dbSession.rollback()
            log("%s %s failed with message: %s" % (self.modelClass, 'insert', err.message))
            raise err
            
    def update(self, objectType, objectID, httpRequest, context, **kwargs):

        targetFrameID = context.viewManager.getFrameID(objectType, 'update')
        formClass = context.contentRegistry.getFormClass(targetFrameID)
        frameObject = context.contentRegistry.getFrame(targetFrameID)
        session = httpRequest.environ[self.sessionName]

        if httpRequest.method == 'GET': 
            object = self.lookup(int(objectID), context.persistenceManager)
            if object is None:
                raise ObjectLookupError(objectType, objectID)
           
            httpRequest.GET['object_id'] = int(objectID)
            displayForm = formClass(None, object)


            kwargs['form'] = displayForm
            kwargs['frame_id'] = targetFrameID
            kwargs['controller_alias'] = objectType

            # Invoke helper function if one has been registered
            helperFunction = context.contentRegistry.getHelperFunctionForFrame(targetFrameID)
            if helperFunction is not None:
                extraData = helperFunction(httpRequest, context)
                kwargs.update(extraData)

            return frameObject.render(httpRequest, context, **kwargs)
        elif httpRequest.method == 'POST':            
            object = self.lookup(int(objectID), context.persistenceManager)
            if object is None:
                raise ObjectLookupError(objectType, objectID)

            inputForm = formClass()
            inputForm.process(httpRequest.POST)
            if not inputForm.validate():
                raise FormValidationError('update', objectType, inputForm.errors)

            inputForm.populate_obj(object)
            try:
                self._update(object, context.persistenceManager)  

                snapback = httpRequest.POST.get('snapback', '').strip()
                if len(snapback):
                    redirectTarget = '/%s/%s' % (context.urlBase, snapback)
                else:
                    redirectTarget = '/%s/controller/%s/index' % (context.urlBase, objectType)

                redirect(redirectTarget)            
            finally:
                session[self.typeSpecificIDSessionTag] = None

    

    
    


