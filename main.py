"""Main Serpentine module for Bottle WSGI stack.


"""


from bottle import route, run, request, response, redirect, static_file

import os
import exceptions
import sys
import traceback
import logging

from db import *
from core import *
from events import *
from reporting import *
from environment import *
from security import *
from snake_eyes import *
from plugin import *


# uncomment the following line to use plugins
from plugin_routes import *


#------ Main module: routing & control --------


@route('/static/:path#.+#')
def serve_static_file(path, environment):
    return static_file(path, root=environment.staticFilePath)


@route('/')
def index(environment):
    # TODO: add full diagnostics to splash page; make splash user-configurable
    redirect("/%s/frame/home" % environment.config['global']['url_base'])


def getAPIMap(environment):    
    configuration = environment.config
    apiReply = {}
    apiReply['app_name'] = environment.getAppName()
    apiReply['app_version'] = environment.getAppVersion()
    apiReply['controller_map'] = environment.frontController.controllerMap
    apiReply['frame_map'] = environment.contentRegistry.frames
    apiReply['helper_list'] = environment.getHelperFunctions()
    apiReply['model_list'] = [ model for model in environment.frontController.controllerMap.keys() ]
    apiReply['responder_map'] = environment.responderMap
    return apiReply
    

@route('/api')
def describe(environment):
    context = Context(environment)
    apiReply = getAPIMap(environment)
    apiFrame = environment.contentRegistry.getFrame('api')
    return apiFrame.render(request, context, **apiReply)



@route('/api/controller/:controllerName', method='GET')
def describeController(environment, controllerName='none'):
    context = Context(environment)
    apiMap = getAPIMap(environment) 
    
    controllerFrame = environment.contentRegistry.getFrame('controller')
    return controllerFrame.render(request, 
                                  context, 
                                  controller = apiMap['controller_map'][controllerName])


@route('/env')
def env(environment):
    return "Placeholder for environment info page"



@route('/login', method='GET')
def invokeLoginGet(environment):
    context = Context(environment)
    try:
        loginFrame = environment.contentRegistry.getFrame('login')
        return loginFrame.render(request, context)
    except Exception, err:
        if err.message == 'HTTP Response 303':  # Bottle does redirects by raising an Exception. Do not catch.
            raise err
        else:
            return displayErrorPage(err, context, environment)



@route('/login', method='POST')
def invokeLoginPost(environment):
    context = Context(environment)
    securityManager = environment.securityManager
    try:
        httpSession = request.environ['beaker.session']
        #raise Exception(httpSession.keys())
        #sessionID = httpSession.id
        securityManager.login(request)
        redirect('/bifrost/frame/home')
    except SecurityException, err:
        return displayErrorPage(err, context, environment)
    


@route('/logout', method='GET')
def invokeLogoutGet(environment):
    securityMgr = environment.securityManager
    securityMgr.clearAuthToken(request)
    redirect(securityMgr.loginRedirectRoute)



@route('/plugin/:pluginID', method='GET')
def identifyPlugin(environment, pluginID='none'):
    response.headers['Cache-Control'] = 'no-cache'

    try:
        context = Context(environment)
        environment.frontController.validate(request)
        plugin = environment.pluginManager.getPlugin(pluginID)
        return plugin.identify(request, context)
    except Exception, err:
        if err.message == 'HTTP Response 303':  # Bottle does redirects by raising an Exception. Do not catch.
            raise err
        else:
            return displayErrorPage(err, context, environment)


@route('/responder/:responderID', method='GET')
def invokeResponderGet(environment, responderID='none'):
    response.headers['Cache-Control'] = 'no-cache'
    
    try:
        context = Context(environment)
        environment.frontController.validate(request)
    
        if not responderID in environment.responderMap:
            raise NoSuchResponderError(responderID)
        
        responder = environment.responderMap[responderID]
        return responder.respond(request, context)
    except Exception, err:
        if err.message == 'HTTP Response 303':  # Bottle does redirects by raising an Exception. Do not catch.
            raise err
        else:
            return displayErrorPage(err, context, environment)
        
    

@route('/uicontrol/:controlID', method='GET')
def invokeUIControlGet(environment, controlID='none'):
    try:
        context = Context(environment)
        environment.frontController.validate(request)
    
        if not controlID in environment.controlMap:
            raise NoSuchUIControlError(controlID)
    
        control = environment.controlMap[controlID]
        params = {}
        params.update(request.GET)
    
        # Invoke helper function if one has been registered
        helper = environment.contentRegistry.getHelperFunctionForFrame(control.templateFrameID)
        if helper:
            extraData = helper(request, context)
            params.update(extraData)
        
        return control.render(request, context, **params)
    except Exception, err:
        if err.message == 'HTTP Response 303':  # Bottle does redirects by raising an Exception. Do not catch.
            raise err
        else:
            return displayErrorPage(err, context, environment)



@route('/frame/:frameID', method='GET')
def handleFrameRequest(environment, frameID='none'):
    response.headers['Cache-Control'] = 'no-cache'
    accessGranted = False
    context = Context(environment)
    try:
        httpSession = request.environ['beaker.session']
        securityMgr = environment.securityManager
        loginRedirectTarget = '/%s/%s' % (environment.urlBase, securityMgr.loginRedirectRoute)
        
        if environment.securityPosture == SecurityPosture.CLOSED:
            # in a CLOSED security posture, all users need an auth token.
            # Papers, please!
            authToken = securityMgr.getAuthToken(request, environment)
            if not authToken:
                # TODO: make this a SECURITY redirect, to hold the user's place 
                # and send them back to the current route once their credentials are
                # in order
                redirect(loginRedirectTarget)
            
            validationStatus = securityMgr.validateObjectRequest(authToken, 
                                                                 frameID, 
                                                                 ObjectType.FRAME, 
                                                                 environment.securityPosture)                                                                 
            if not validationStatus.ok:
                objectRedirectTarget = '/%s/%s' % (environment.getAppRoot(), validationStatus.redirectRoute)
                redirect(objectRedirectTarget)                                        
        else:
            # in an OPEN security posture, user only needs an auth token 
            # when accessing a secured object
            
            if securityMgr.objectIsSecured(frameID, ObjectType.FRAME):
                authToken = securityMgr.getAuthToken(request, environment)
                if not authToken:
                    redirect(loginRedirectTarget)

                validationStatus = securityMgr.validateObjectRequest(authToken, 
                                                                    frameID, 
                                                                    ObjectType.FRAME, 
                                                                    ActionType.RENDER, 
                                                                    environment.securityPosture)                
                if not validationStatus.ok:                    
                    objectRedirectTarget = '/%s/%s' % (environment.getURLBase(), validationStatus.redirectRoute)                    
                    redirect(objectRedirectTarget)                                        
           
        # If they've made it here without being redirected, they're OK     
        frameArgs ={}
        # this frame  may or may not have an associated Form
        inputForm = None
    
        if environment.contentRegistry.hasForm(frameID):        
            inputFormClass = environment.contentRegistry.getFormClass(frameID)
            if inputFormClass:
                # get whatever data was passed to us
                inputForm = inputFormClass()
                inputForm.process(request.GET)     
                frameArgs['form'] = inputForm
    
        # Invoke helper function if one has been registered
        helper = environment.contentRegistry.getHelperFunctionForFrame(frameID)
        if helper:
            extraData = helper(request, context)
            frameArgs.update(extraData)
    
        frameArgs['frame_id'] = frameID
        return environment.contentRegistry.getFrame(frameID).render(request, context, **frameArgs)
    except Exception, err:
        if err.message == 'HTTP Response 303':  # Bottle does redirects by raising an Exception. Do not catch.
            raise err
        else:
            return displayErrorPage(err, context, environment)


@route('/report/:reportID', method='GET')
def generateReport(environment, reportID = 'none'):
    try:
        context = Context(environment)
        reportMgr = environment.reportManager
        return reportMgr.runReport(reportID, request, context)
    except Exception, err:
        if err.message == 'HTTP Response 303':  # Bottle does redirects by raising an Exception. Do not catch.
            raise err
        else:
            return displayErrorPage(err, context, environment)


@route('/event/:eventtype')
def handleEvent(environment, eventtype = 'none'):
    # TODO: use eventlet here
    newEvent = Event(eventtype, { 'time' : 'now', 'place' : 'here' })
    try:
        context = Context(environment)
        status = environment.dispatcher.handleEvent(newEvent)
        return str(status)
    except Exception, err:
        if err.message == 'HTTP Response 303':  # Bottle does redirects by raising an Exception. Do not catch.
            raise err
        else:
            return displayErrorPage(err, context, environment)



#
# Invoking the controller update() in this mode looks up the object with the specified ID
# and prepopulates its data-entry form.
#
@route('/controller/:objectType/update/:objectID', method='GET')
def invokeControllerUpdateGet(environment, objectType = 'none', objectID = 'none'):
    
    try:
        context = Context(environment)
        environment.frontController.validate(request)
    
        # Get the controller for the type in question
        controller = environment.frontController.getController(objectType)
        session = request.environ[controller.sessionName]
        session[controller.typeSpecificIDSessionTag] = objectID
        return controller.update(objectID, request, context)
    except Exception, err:
        if err.message == 'HTTP Response 303':  # Bottle does redirects by raising an Exception. Do not catch.
            raise err
        else:
            return displayErrorPage(err, context, environment)
    
        
            
#
# Invoking the controller update() in this mode triggers the actual database operation 
# and saves the changed object.
#
@route('/controller/:objectType/update', method='POST')
def invokeControllerUpdatePost(environment, objectType= 'none', objectID = 'none'):
    
    try:
        context = Context(environment)    
        environment.frontController.validate(request)
        controller = environment.frontController.getController(objectType)
    
        session = request.environ['beaker.session']
        objectID = session.get(controller.typeSpecificIDSessionTag)
        if objectID is None:
            raise Exception("Update failed: No %s ID in session data." % objectType)
    
        return controller.update(objectID, request, context)
    except Exception, err:
        if err.message == 'HTTP Response 303':  # Bottle does redirects by raising an Exception. Do not catch.
            raise err
        else:
            return displayErrorPage(err, context, environment)



@route('/controller/:objectType/update/:objectID', method='POST')
def invokeControllerUpdatePost(environment, objectType = 'none', objectID = 'none'):

    try:
        context = Context(environment)    
        environment.frontController.validate(request)
        controller = environment.frontController.getController(objectType)    
        return controller.update(objectID, request, context)
    except Exception, err:
        if err.message == 'HTTP Response 303':  # Bottle does redirects by raising an Exception. Do not catch.
            raise err
        else:
            return displayErrorPage(err, context, environment)

#
# Brings up the delete confirmation page.
#
@route('/controller/:objectType/delete/:objectID', method='GET')
def invokeControllerDeleteGet(environment, objectType='none', objectID='none'):

    try:
        context = Context(environment)    
        environment.frontController.validate(request)
        controller = environment.frontController.getController(objectType)
        targetFrameID = context.viewManager.getFrameID(objectType, 'delete')
        
        formClass = context.contentRegistry.getFormClass(targetFrameID)
        frameObject = context.contentRegistry.getFrame(targetFrameID)
    
        dbSession = context.persistenceManager.getSession()
        obj = controller.lookup(int(objectID), dbSession, context.persistenceManager)
        dbSession.close()
        
        if not obj:
            raise ObjectLookupError(objectType, objectID)
        
        
        mode = request.GET.get('mode', '').strip()
        if mode == 'bypass':
            return controller.delete(obj.id, request, context, controller_alias=objectType)
            
        
        
        request.GET['object_id'] = int(objectID)
        displayForm = formClass(None, obj)
       
        frameArgs = {}
        frameArgs['controller'] = controller
        frameArgs['form'] = displayForm
        frameArgs['frame_id'] = targetFrameID
        frameArgs['controller_alias'] = objectType
        frameArgs['url_base'] = environment.urlBase
        
        # Invoke helper function if one has been registered
        helper = environment.contentRegistry.getHelperFunctionForFrame(targetFrameID)
        if helper is not None:
            extraData = helper(request, context)
            frameArgs.update(extraData)
            
        frameObject = context.contentRegistry.getFrame(targetFrameID)
        return frameObject.render(request, context, **frameArgs)
    except Exception, err:
        if err.message == 'HTTP Response 303':  # Bottle does redirects by raising an Exception. Do not catch.
            raise err
        else:
            return displayErrorPage(err, context, environment)


#
# Invokes the delete() method on the controller for the selected type.
#
@route('/controller/:objectType/delete/:objectID', method='POST')
def invokeControllerDeletePost(environment, objectType='none', objectID='none'):    
    try:
        context = Context(environment)    
        environment.frontController.validate(request)
        controller = environment.frontController.getController(objectType)    
        return controller.delete(objectID, request, context)
    except Exception, err:
        if err.message == 'HTTP Response 303':  # Bottle does redirects by raising an Exception. Do not catch.
            raise err
        else:
            return displayErrorPage(err, context, environment)
            
#
# Invokes the index() method on the controller for the selected type.
#
@route('/controller/:objectType/index')
def invokeControllerIndex(environment, objectType = 'none'): 
    try:
        context = Context(environment);
        environment.frontController.validate(request)
        # Get the controller for the type in question
        controller = environment.frontController.getController(objectType)
        return controller.index(request, context)
    except Exception, err:
        if err.message == 'HTTP Response 303':  # Bottle does redirects by raising an Exception. Do not catch.
            raise err
        else:
            return displayErrorPage(err, context, environment)


#
# A nonspecific controller invocation triggers index by default
#
@route('/controller/:objectType')
def invokeControllerIndexDefault(environment, objectType = 'none'):
    
    return invokeControllerIndex(environment, objectType)


#
# Invokes the index() method, with pagination
#    
@route('/controller/:objectType/index/page/:pageNum')
def invokeControllerIndexPaging(environment, objectType = 'none', pageNum = 'none'):
    try:
        context = Context(environment);
        environment.frontController.validate(request)
        controller = environment.frontController.getController(objectType)
    
        pageNumInt = int(pageNum)
        if pageNumInt < 1:
            raise InvalidPageNumberError()
    
        return controller.indexPage(int(pageNum), request, context)
    except Exception, err:
        if err.message == 'HTTP Response 303':  # Bottle does redirects by raising an Exception. Do not catch.
            raise err
        else:
            return displayErrorPage(err, context, environment)

#
# Issuing a controller insert() will either display a form or perform an insert,
# depending on whether it is issued as a POST or GET
#
@route('/controller/:objectType/insert', method = 'GET')
def invokeControllerInsertGet(environment, objectType = 'none'):
    try:
        context = Context(environment)    
        environment.frontController.validate(request)
        controller = environment.frontController.getController(objectType)
        frameID = context.viewManager.getFrameID(objectType, 'insert')
       
        inputFormClass = context.contentRegistry.getFormClass(frameID) # will raise exception if no form exists
        inputForm = inputFormClass()
        inputForm.process(request.GET) 
        
    
        frameArgs = {}
        frameArgs['controller'] = controller
        frameArgs['form'] = inputForm
        frameArgs['frame_id'] = frameID
        frameArgs['controller_alias'] = objectType
    
        # Invoke helper function if one has been registered
        helper = environment.contentRegistry.getHelperFunctionForFrame(frameID)
        if helper is not None:
            extraData = helper(request, context)
            frameArgs.update(extraData)
            
        frameObject = context.contentRegistry.getFrame(frameID)
        return frameObject.render(request, context, **frameArgs)
    except Exception, err:
        if err.message == 'HTTP Response 303':  # Bottle does redirects by raising an Exception. Do not catch.
            raise err
        else:
            return displayErrorPage(err, context, environment)



@route('/controller/:objectType/insert', method = 'POST')
def invokeControllerInsertPost(environment, objectType = 'none'):
    try:
        context = Context(environment)    
        environment.frontController.validate(request)
        controller = environment.frontController.getController(objectType)
    
        return controller.insert(request, context)
    except Exception, err:
        if err.message == 'HTTP Response 303':  # Bottle does redirects by raising an Exception. Do not catch.
            raise err
        else:
            return displayErrorPage(err, context, environment)


@route('/controller/:objectType/:controllerMethod', method = 'POST')
def invokeControllerMethodPost(environment, objectType='none', controllerMethod='none'):
        
    try:
        context = Context(environment);
        environment.frontController.validate(request)
    
        # Get the controller for the type in question
        targetController = environment.frontController.getController(objectType)
        targetMethod = getattr(targetController, controllerMethod, None)
        
        if callable(targetMethod):        
            return targetMethod(request, context, controller_alias=objectType)            
        else:
            raise NoControllerMethodError(controllerMethod, objectType)
    except Exception, err:
        if err.message == 'HTTP Response 303':  # Bottle does redirects by raising an Exception. Do not catch.
            raise err
        else:
            return displayErrorPage(err, context, environment)



@route('/controller/:objectType/:controllerMethod', method='GET')
def invokeControllerMethodGet(environment, objectType='none', controllerMethod='none'):

    response.header['Cache-Control'] = 'no-cache'
    response.header['Expires'] = 0

    try:
        context = Context(environment);
        environment.frontController.validate(request)
    
        # Get the controller for the type in question
        targetController = environment.frontController.getController(objectType)
        targetMethod = getattr(targetController, controllerMethod, None)
        if callable(targetMethod):
    
            mode = request.GET.get('mode', '').strip()
            if mode == 'bypass':
                return targetMethod(request, context, controller_alias=objectType)
    
            
            targetFrameID = environment.viewManager.getFrameID(objectType, controllerMethod)    
            frameObject = environment.contentRegistry.getFrame(targetFrameID)
            context.frame = frameObject
    
            inputForm = None
            if environment.contentRegistry.hasForm(targetFrameID):            
                inputFormClass = environment.contentRegistry.getFormClass(targetFrameID)
                inputForm = inputFormClass()
                inputForm.process(request.GET)
    
            frameArgs = {}
            frameArgs['form'] = inputForm
            frameArgs['frame_id'] = targetFrameID
            frameArgs['controller_alias'] = objectType
    
            # Invoke helper function if one has been registered
            helper = environment.contentRegistry.getHelperFunctionForFrame(targetFrameID)
            if helper is not None:
                extraData = helper(request, context)
                frameArgs.update(extraData)
            
            return frameObject.render(request, context, **frameArgs)
        else:
            raise NoControllerMethodError(controllerMethod, objectType)
            
    except Exception, err:
        if err.message == 'HTTP Response 303':  # Bottle does redirects by raising an Exception. Do not catch.
            raise err
        else:
            return displayErrorPage(err, context, environment)
