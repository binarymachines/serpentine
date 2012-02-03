"""Main Serpentine module for Bottle WSGI stack.


"""


from bottle import route, run, request, response, redirect, static_file

import os
import exceptions
import sys
import logging

from db import *
from core import *
from events import *
from reporting import *
from environment import *



#------ Main module: routing & control --------


from bottle import static_file
@route('/static/:path#.+#')
def serve_static_file(path, environment):
    return static_file(path, root=environment.staticFilePath)

@route('/')
def index(environment):
    # TODO: add full diagnostics to splash page; make splash user-configurable
    redirect("/%s/static/main.html" % environment.config['global']['url_base'])


def getAPIMap(environment):
    
    configuration = environment.config
    apiReply = {}

    apiReply['app_name'] = environment.appName
    apiReply['app_version'] = environment.appVersion
    apiReply['controller_map'] = environment.frontController.controllerMap
    apiReply['frame_map'] = environment.contentRegistry.frames
    apiReply['helper_list'] = environment.getHelperFunctions()
    apiReply['model_list'] = [ model for model in environment.frontController.controllerMap.keys() ]
    apiReply['responder_map'] = environment.responderMap

    apiReply['controller_frame'] = environment.controllerFrame

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
    

@route('/responder/:responderID', method='GET')
def invokeResponderGet(environment, responderID='none'):

    response.header['Cache-Control'] = 'no-cache'
    

    context = Context(environment)
    environment.frontController.validate(request)

    if not responderID in environment.responderMap:
        raise NoSuchResponderError(responderID)


    responder = environment.responderMap[responderID]
    return responder.respond(request, context)

"""
@route('/receiver/:receiverID', method='POST')
def invokeReceiverPost(environment, receiverID='none'):
    context = Context(environment)
    environment.frontController.validate(request)

    if not receiverID in environment.receiverMap:
        raise NoSuchReceiverError(receiverID)

    receiver = environment.receiverMap[receiverID]
    return receiver.process(request, context)
"""


@route('/frame/:frameID')
def handleFrameRequest(environment, frameID='none'):
    response.header['Cache-Control'] = 'no-cache'
    

    context = Context(environment)
    frameArgs ={}
    # this frame  may or may not have an associated Form
    inputForm = None

    if environment.contentRegistry.hasForm(frameID):        
        inputFormClass = environment.contentRegistry.getFormClass(frameID)
        if inputFormClass is not None:
            # get whatever data was passed to us
            inputForm = inputFormClass()
            inputForm.process(request.GET)     
            frameArgs['form'] = inputForm

    # Invoke helper function if one has been registered
    helper = environment.contentRegistry.getHelperFunctionForFrame(frameID)
    if helper is not None:
        extraData = helper(request, context)
        frameArgs.update(extraData)

    frameArgs['frame_id'] = frameID
    return environment.contentRegistry.getFrame(frameID).render(request, context, **frameArgs)


@route('/report/:reportID', method='GET')
def generateReport(environment, reportID = 'none'):
    context = Context(environment)
    reportMgr = environment.reportManager
    return reportMgr.runReport(reportID, request, context)



@route('/event/:eventtype')
def handleEvent(environment, eventtype = 'none'):
    newEvent = Event(eventtype, { 'time' : 'now', 'place' : 'here' })
    try:
        status = environment.dispatcher.handleEvent(newEvent)
        return str(status)
    except EventDispatchError as err:
        return str(err)
    except:
        print sys.exc_info()

#
# Invoking the controller update() in this mode looks up the object with the specified ID
# and prepopulates its data-entry form.
#
@route('/controller/:objectType/update/:objectID', method='GET')
def invokeControllerUpdateGet(environment, objectType = 'none', objectID = 'none'):
    
    context = Context(environment)
    environment.frontController.validate(request)

    # Get the controller for the type in question
    controller = environment.frontController.getController(objectType)
    session = request.environ[controller.sessionName]
    session[controller.typeSpecificIDSessionTag] = objectID
    return controller.update(objectType, objectID, request, context)
    
#
# Invoking the controller update() in this mode triggers the actual database operation 
# and saves the changed object.
#
@route('/controller/:objectType/update', method='POST')
def invokeControllerUpdatePost(environment, objectType= 'none', objectID = 'none'):
    
    context = Context(environment)    
    environment.frontController.validate(request)
    controller = environment.frontController.getController(objectType)

    session = request.environ['beaker.session']
    objectID = session.get(controller.typeSpecificIDSessionTag)
    if objectID is None:
        raise Exception("Update failed: No %s ID in session data." % objectType)

    return controller.update(objectType, objectID, request, context)
        
            
#
# Invokes the index() method on the controller for the selected type.
#
@route('/controller/:objectType/index')
def invokeControllerIndex(environment, objectType = 'none'): 
    
    context = Context(environment);
    environment.frontController.validate(request)
    # Get the controller for the type in question
    controller = environment.frontController.getController(objectType)
    return controller.index(objectType, request, context)

#
# Invokes the index() method, with pagination
#    
@route('/controller/:objectType/index/page/:pageNum')
def invokeControllerIndexPaging(environment, objectType = 'none', pageNum = 'none'):
    context = Context(environment);
    environment.frontController.validate(request)
    controller = environment.frontController.getController(objectType)

    pageNumInt = int(pageNum)
    if pageNumInt < 1:
        raise InvalidPageNumberError()

    return controller.indexPage(objectType, int(pageNum), request, context)


#
# Issuing a controller insert() will either display a form or perform an insert,
# depending on whether it is issued as a POST or GET
#
@route('/controller/:objectType/insert', method = 'GET')
def invokeControllerInsertGet(environment, objectType = 'none'):

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


@route('/controller/:objectType/insert', method = 'POST')
def invokeControllerInsertPost(environment, objectType = 'none'):
    
    context = Context(environment)    
    environment.frontController.validate(request)
    controller = environment.frontController.getController(objectType)

    return controller.insert(objectType, request, context)


@route('/controller/:objectType/:controllerMethod', method = 'POST')
def invokeControllerMethodPost(environment, objectType='none', controllerMethod='none'):
    
    response.header['Cache-Control'] = 'no-cache'
    response.header['Expires'] = 0

    context = Context(environment);
    environment.frontController.validate(request)

    # Get the controller for the type in question
    targetController = environment.frontController.getController(objectType)
    targetMethod = getattr(targetController, controllerMethod, None)
    
    if callable(targetMethod):        
        return targetMethod(request, context, controller_alias=objectType)            
    else:
        return NoControllerMethodError(controllerMethod, objectType).message
    

@route('/controller/:objectType/:controllerMethod', method='GET')
def invokeControllerMethodGet(environment, objectType='none', controllerMethod='none'):

    response.header['Cache-Control'] = 'no-cache'
    response.header['Expires'] = 0

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
        return NoControllerMethodError(controllerMethod, objectType).message
