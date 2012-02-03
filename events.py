#
#------ Event module --------
#

import os
import exceptions
import sys

class EventDispatchError(exceptions.Exception):
    def __init__(self, event):
        self.event = event

    def __str__(self):
        return "No event handler registered to handle event type: %s" % self.event.getType()



class Event:
    def __init__(self, type, paramDictionary):
        self.type = type
        self.paramDict = paramDictionary

    def getType(self):
        return self.type

    def getParams(self):
        return self.paramDict


class EventHandlerStatus:
    def __init__(self, eventType, ok = True, errMessage = None):
        self.eventType = eventType
        self.isok = ok
        self.message = errMessage

    def __str__(self):
        return "[event type: %s ] handler returned %s | message: %s" % (self.eventType, self.ok, self.message) 


class EventHandler:
    def __init__(self):
        self.paramMap = {}

    def handleEvent(self, event):
        return EventHandlerStatus(event.getType()) # default response is OK

    
class EventDispatcher:
    def __init__(self):
        self.dispatchTable = {}
    
    def registerHandler(self, eventType, eventHandler):
        self.dispatchTable[eventType] = eventHandler

    def unregisterHandler(self, eventType):
        self.dispatchTable[eventType] = None

    def handleEvent(self, event):
        if not self.dispatchTable.has_key(event.getType()):
            print "No event handler, time to throw an exception..."
            raise EventDispatchError(event)
        else:
            handler = self.dispatchTable[event.getType()]
            return handler.handleEvent(event)


