#!/bin/env python

from bottle import request
import sys, traceback

def displayErrorPage(exception, context, environment):
    exc_traceback = sys.exc_info()        
    stackTrace = traceback.extract_tb(exc_traceback[2])
        
    errorFrame = environment.contentRegistry.getFrame('error_frame')
    frameArgs = { 'exception': exception, 'stacktrace': stackTrace }
    return errorFrame.render(request, context, **frameArgs)
