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
        self.errors = ['%s: %s'%(key, errorDict[key]) for key in errorDict]
        
        Exception.__init__(self,
                           'Form validation for %s %s failed with errors \
                           in the following fields: %s.' \
                           % (objectType, operation, ','.join(self.errors)))


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



class DatatypeConverter(object):
 
    converters = { 'int': int, 'float': float, 'string': str }
    
    @classmethod
    def convert(pClass, data, typeName):
        converter = pClass.converters.get(typeName, None)
        if converter:
            return converter(data) 
        return data
        
        
class Datatype(object):
    INT = 'int'
    FLOAT = 'float'
    STRING = 'str'        


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


class ClassLoader:
    def __init__(self):
        self.cache = {}

    def loadClass(self, fqClassName):  # fully qualified class name in the form moduleName.className
        result = self.cache.get(fqClassName)
        if not result == None:
            return result
        else:
            try:
                  log('>> Receiving classname for loading: %s' % fqClassName)
                  paths = fqClassName.split('.')
                  moduleName = '.'.join(paths[:-1])
                  className = paths[-1]
                  result = getattr(__import__(moduleName), className)
                  self.cache[fqClassName] = result
                  return result
            except AttributeError:
                  raise ClassLoaderError(fqClassName)


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


class HttpUtility(object):
    @classmethod 
    def getRequiredParameter(pClass, paramName, paramTypeString, httpRequestData):
    
        requestData = httpRequestData.get(paramName, None)
        if requestData is None:
            raise MissingRequestParamError(paramName)
            
        value = DatatypeConverter.convert(requestData, paramTypeString)
        return value
    


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
        
        self.postCompletionDispatchTable = {}
        self.postCompletionDispatchTable['insert'] = self._defaultPostCompletionMethod
        self.postCompletionDispatchTable['update'] = self._defaultPostCompletionMethod
        self.postCompletionDispatchTable['delete'] = self._defaultPostCompletionMethod
        

    def lookup(self, objectID, dbSession):
        try:            
            object = dbSession.query(self.modelClass).filter(self.modelClass.id == objectID).one()           
            return object
            
        except NoResultFound, err:
            raise Exception('No %s instance found in DB with primary key %s.' % (self.modelClass.__name__, str(objectID)))
            
        except SQLAlchemyError, err:
            
            log('%s lookup failed with message: %s' % (self.modelClass.__name__, err.message))
            # TODO: scaffolding to track down lookup 
            raise err

    
    
    def _postCompletionExec(self, methodName, httpRequest, context, **kwargs):
        
        dispatchTarget = self.postCompletionDispatchTable.get(methodName, None)
        if not dispatchTarget:            
            return # OK to fail quietly?
        else:    
            #raise Exception('Calling _defaultPostCompletionMethod with method name %s' % methodName)
            dispatchTarget(httpRequest, context, **kwargs)
    
    
    
    def _defaultPostCompletionMethod(self, httpRequest, context, **kwargs):    
        snapback = httpRequest.params.get('snapback')
        if snapback:
            redirectTarget = '/%s/%s' % (context.urlBase, snapback.strip())
        else:
            redirectTarget = '/%s/controller/%s/index' % (context.urlBase, self.modelClass.__name__)
    
        redirect(redirectTarget)
    
    
    
    def lookup(self, objectID, dbSession, persistenceManager):
        
        try:            
            object = dbSession.query(self.modelClass).filter(self.modelClass.id == objectID).one()            
            return object
        except SQLAlchemyError, err:
            log('Object lookup failed with message: %s' % err.message)
            # TODO: scaffolding to track down lookup 
            # should we raise err? Is not finding an object an exceptional condition?
            return None
        
            
     
        
    def assertObjectExists(self, modelName, objectID, persistenceManager):
        dbSession = persistenceManager.getSession()
        result =  self.lookup(objectID, dbSession, persistenceManager) 
        dbSession.close()
        if result is None:
            raise ObjectLookupError(self.modelClass.__name__, objectID)
        
        
        
    def _index(self, dbSession, persistenceManager):        
        try:            
            query =  dbSession.query(self.modelClass)  
            collection = query.all()                 
            return collection
        except SQLAlchemyError, err:
            dbSession.rollback()
            log("%s %s failed with message: %s" % (self.modelClass, 'index', err.message))
            raise err
        


    def _indexPage(self, dbSession, persistenceManager, pageNumber, pageSize):
        try:            
            offset = (pageNumber - 1) * pageSize
            query =  dbSession.query(self.modelClass).limit(pageSize).offset(offset)
            collection = query.all()        
            return collection
        except SQLAlchemyError, err:
            dbSession.rollback()
            log("%s %s failed with message: %s" % (self.modelClass, 'index', err.message))
            raise err
        


    def index(self, httpRequest, context, **kwargs):
        
        frameID = context.viewManager.getFrameID(self.modelClass.__name__, 'index')
        frameObject = context.contentRegistry.getFrame(frameID)
        
        # this is so that the render() call to the underlying XMLFrame object can look up its stylesheet
        httpRequest.params['frame'] = frameID   
        dbSession = context.persistenceManager.getSession()
        
        try:
            collection = self._index(dbSession, context.persistenceManager)
            kwargs['resultset'] = collection # TODO: rethink the variable name

            # Invoke helper function if one has been registered
            helperFunction = context.contentRegistry.getHelperFunctionForFrame(frameID)
            if helperFunction is not None:
                extraData = helperFunction(httpRequest, context)
                kwargs.update(extraData)

            return frameObject.render(httpRequest, context, **kwargs)
        finally:
            dbSession.close()

    # TODO: fix security hole, ensure pageNumber is an integer and a reasonable value

    def indexPage(self, pageNumber, httpRequest, context, **kwargs):

        frameID = context.viewManager.getFrameID(self.modelClass.__name__, 'index')
        frameObject = context.contentRegistry.getFrame(frameID)
        
        # this is so that the render() call to the underlying XMLFrame object can look up its stylesheet
        httpRequest.params['frame'] = frameID   
         
        #
        # TODO: for now we hardcode the page size, but eventually we'll get it from the context object,
        # which in turn will read it from the config file.
        #
        pageSize = 50 # this is the number of records we show on a page

        dbSession = context.persistenceManager.getSession()
        try:
            collection = self._indexPage(session, context.persistenceManager, pageNumber, pageSize) 
            kwargs['resultset'] = collection # TODO: rethink the variable name

            # Invoke helper function if one has been registered
            helperFunction = context.contentRegistry.getHelperFunctionForFrame(frameID)
            if helperFunction is not None:
                extraData = helperFunction(httpRequest, context)
                kwargs.update(extraData)

            return frameObject.render(httpRequest, context, **kwargs)
        finally:
            dbSession.close()


    def _insert(self, object, dbSession, persistenceManager):        
        try:            
            dbSession.add(object) 
            dbSession.flush()
            return object
        except SQLAlchemyError, err:    
            dbSession.rollback()
            log("%s failed with message: %s" % ('insert', err.message))
            raise err        
        
    
    def insert(self, httpRequest, context, **kwargs):
        
        objectType = self.modelClass.__name__
        
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
        dbSession = context.persistenceManager.getSession()
        try:
            self._insert(object, dbSession, context.persistenceManager)
            dbSession.commit()
            
            self._postCompletionExec('insert', httpRequest, context, **kwargs)
            '''
            snapback = httpRequest.POST.get('snapback', '').strip()
            if len(snapback):
                redirectTarget = '/%s/%s' % (context.urlBase, snapback)
            else:
                redirectTarget = '/%s/controller/%s/index' % (context.urlBase, objectType)

            redirect(redirectTarget)
            '''
        except Exception, err:
            dbSession.rollback()
            raise err
        finally:
            dbSession.close()
        
    def _delete(self, object, dbSession, persistenceManager):
        
        
        try:
            dbSession.delete(object)
            #setattr(object, "deleted", True)       
            
            dbSession.flush()
            dbSession.commit()
        except SQLAlchemyError, err:
            dbSession.rollback()
            log("%s %s failed with message: %s" % (self.modelClass, 'delete', err.message))
            raise err 
    

    def delete(self, objectID, httpRequest, context, **kwargs):
    
        objectType = self.modelClass.__name__
        pMgr = context.persistenceManager
        dbSession = pMgr.getSession()
        
        try:
            targetObject = self.lookup(int(objectID), dbSession, pMgr)
            self._delete(targetObject, dbSession, pMgr)  
            dbSession.commit() 
                        
            self._postCompletionExec('delete', httpRequest, context, **kwargs)
            
            '''
            snapback = httpRequest.GET.get('snapback', '').strip()
            if len(snapback):
                redirectTarget = '/%s/%s' % (context.urlBase, snapback)
            else:
                redirectTarget = '/%s/controller/%s/index' % (context.urlBase, objectType)
        
            redirect(redirectTarget)    
            ''' 
                    
        except Exception, err:
            dbSession.rollback()
            raise err
        finally:
            dbSession.close()
        
    

    def _update(self, object, dbSession, persistenceManager):       
        try:
            dbSession.flush()             
            
        except SQLAlchemyError, err:
            dbSession.rollback()
            log("%s %s failed with message: %s" % (self.modelClass, 'insert', err.message))
            raise err       
        
            
            
    def update(self, objectID, httpRequest, context, **kwargs):

        objectType = self.modelClass.__name__
        
        targetFrameID = context.viewManager.getFrameID(objectType, 'update')
        formClass = context.contentRegistry.getFormClass(targetFrameID)
        frameObject = context.contentRegistry.getFrame(targetFrameID)
        session = httpRequest.environ[self.sessionName]

        pMgr = context.persistenceManager
        dbSession = pMgr.getSession()
        
        obj = self.lookup(int(objectID), dbSession, pMgr)
        if obj is None: 
            dbSession.close()           
            raise ObjectLookupError(objectType, objectID)

        if httpRequest.method == 'GET': 
            try:
                httpRequest.GET['object_id'] = int(objectID)
                displayForm = formClass(None, obj)
    
                kwargs['form'] = displayForm
                kwargs['frame_id'] = targetFrameID
                kwargs['controller_alias'] = objectType
    
                # Invoke helper function if one has been registered
                helperFunction = context.contentRegistry.getHelperFunctionForFrame(targetFrameID)
                if helperFunction is not None:
                    extraData = helperFunction(httpRequest, context)
                    kwargs.update(extraData)
                
                return frameObject.render(httpRequest, context, **kwargs)
            finally:
                dbSession.close()
                
                
        elif httpRequest.method == 'POST':     
            try:
                inputForm = formClass()
                inputForm.process(httpRequest.POST)
                if not inputForm.validate():
                    raise FormValidationError('update', objectType, inputForm.errors)
    
                inputForm.populate_obj(obj)
                
                self._update(obj, dbSession, context.persistenceManager)
                dbSession.commit()
                
                self._postCompletionExec('update', httpRequest, context, **kwargs)
                
                '''
                snapback = httpRequest.POST.get('snapback', '').strip()
                if len(snapback):
                    redirectTarget = '/%s/%s' % (context.urlBase, snapback)
                else:
                    redirectTarget = '/%s/controller/%s/index' % (context.urlBase, objectType)            
                redirect(redirectTarget)  
                '''  
            except Exception, err:
                dbSession.rollback()
                raise err         
            finally:
                session[self.typeSpecificIDSessionTag] = None                
                dbSession.close()

    

    



