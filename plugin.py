#---------------------------------------------------------------------
#
# plugin.py: Support for user-defined plugins in Serpentine
#
# Dexter Taylor
# binarymachineshop@gmail.com
# github: binarymachines
#
#
#
#---------------------------------------------------------------------

"""

The config file section responsible for plugin initialization
follows this pattern:

plugins:
	foobar:
		class: MyPlugin
		slots:
			- method:	doSomething
			  route:  	ds/:variable
			  request_type:	GET

			- method:	doSomethingElse
			  route:	dse/:variable
			  request_type: GET


where each 'slot' specifies the plugin method to be called,
the URL route (really an extension of the plugin's default route,
which is always http://<base_url>:<port>/<app_name>/plugin/<plugin_alias>,
so that the first slot in the example above can be accessed by issuing

http://<base_url>:<port>/<app_name>/plugin/foobar/ds/<variable_value>

"""



from bottle import route, run, request, response, redirect, static_file

import os, sys
import re


class NoSuchAdapterMethodError(Exception):
      def __init__(self, adapterClassName, routeExtensionString, targetMethodName):
            Exception.__init__(self,
                               'Attempted to add invalid route extension %s to Adapter class %s: class has no method %s.' \
                  % (routeExtensionString, adapterClassName, targetMethodName))


class InvalidRouteElementError(Exception):
      def __init__(self, routeExtensionString):
            Exception.__init__(self, 
                               'Attempted to create invalid route element "%s": extension string contains forbidden URL characters.' \
                  % (routeExtensionString))
      


class PluginInitError(Exception):
      def __init__(self, pluginIDString, statusMessage):
            Exception.__init__(self,
                               'Error initializing plugin with alias "%s": the Adapter failed to initialize with error "%s".' \
                  % (pluginIDString, statusMessage))
            


class RouteElement(object):
      def __init__(self, elementString, positionIndex):
            self.elementStringRX = re.compile(r'^[a-zA-Z0-9_-]+$')
            self.elementString = elementString
            self.positionIndex = positionIndex

      def _isValid(self):
            return self.elementStringRX.match(self.elementString) is not None

      def isStatic(self):
            pass



class StaticRouteElement(RouteElement):
      def __init__(self, elementString, positionIndex):
            RouteElement.__init__(self, elementString, positionIndex)
            if not self._isValid():
                  raise InvalidRouteElementString(self.__class__.__name__, extensionString)
                  
      def isStatic(self):
            return True


class VariableRouteElement(RouteElement):
      def __init__(self, elementString, positionIndex):
            RouteElement.__init__(self, elementString, positionIndex)
            if not self._isValid():
                  raise InvalidRouteElementString(self.__class__.__name__, elementString)

      def isStatic(self):
            return False
            


class RouteExtension(object):

      varExtensionRX = re.compile(r'^[:]{1}[a-zA-Z0-9_-]+$')
      staticExtensionRX = re.compile(r'^[a-zA-Z0-9_-]+$')
      
      def __init__(self, extensionString):            
            # remove duplicate slashes
            s = re.sub(r'[/]+', '/', extensionString) 

            # remove leading and trailing slashes
            if s.startswith('/'):
                  s = s[1:]
            if s.endswith('/'):
                  s = s[:-1]
            self.string = s
            
            self.elements = []
            tokens = [t for t in self.string.split('/') if t]
            positionIndex = 1
            for t in tokens:
                  if not t:
                        continue
                  if self.__class__.varExtensionRX.match(t):
                        self.elements.append(VariableRouteElement(t[1:], positionIndex))
                  elif self.__class__.staticExtensionRX.match(t):
                        self.elements.append(StaticRouteElement(t, positionIndex))
                  else:
                        raise InvalidRouteElementError(extensionString)
                  
                  positionIndex = positionIndex + 1
                  
      def __iter__(self):
            return iter(self.elements)


      def __repr__(self):
            return self.string


      def add(self, routeExtensionString):
            self.elements.expand(RouteExtension(routeExtensionString).elements)
            return self


      def getVariableNames(self):
            return [e.elementString for e in self.elements if not e.isStatic]

      variableNames = property(getVariableNames)


class Slot(object):
      def __init__(self, pluginID, pluginMethodName, routeExtension, httpMethod):
            self.pluginID = pluginID
            self.pluginMethodName = pluginMethodName
            self.routeExtension = routeExtension
            self.httpMethod = httpMethod
            self.variables = []
            for element in routeExtension:
                  print 'Processing route extension element %s...' % element
                  if not element.isStatic():
                        self.variables.append(element.elementString)

      
      def writeFunctionName(self):
            pluginString = self.pluginID.capitalize()
            methodString = self.pluginMethodName.capitalize()
            requestTypeString = self.httpMethod.lower().capitalize()
            return 'invoke%sPluginMethod%s%s' % (pluginString, methodString, requestTypeString)


      def writeFunctionSignature(self):
            return 'environment, %s' % (', '.join("%s = 'none'" % variable for variable in self._variables))
      
      functionName = property(writeFunctionName)
      functionSignature = property(writeFunctionSignature)


class Plugin(object):
      def __init__(self):            
            self.status = ''


      def id(self, **kwargs):
            # override in subclasses. Return signature content or plugin documentation.
            pass

      
      def initialize(self, **kwargs):
            # override in subclasses. Return True on success. 
            return False


     
class PluginManager(object):
      def __init__(self):
            self.registry = {}
            self._slots = {}

            
      def registerPlugin(self, plugin, alias, **kwargs):
            try:
                  if plugin.initialize(**kwargs):
                        self.registry[alias] = plugin                        
                  else:
                        raise Exception(plugin.statusMessage)
            except Exception, err:
                  raise PluginInitError(alias, err.message)


      def addSlot(self, pluginAlias, pluginMethodName, routeExtensionString, httpMethod):
            plugin = self.registry.get(pluginAlias)
            if not plugin:
                  raise NoSuchPluginException(pluginAlias)

            routeExtension = RouteExtension(routeExtensionString)
            newSlot = Slot(pluginAlias, pluginMethodName, routeExtension, httpMethod)
            self._slots[pluginAlias] = newSlot


      def getPlugin(self, pluginIDString):
            if not self.registry.get(pluginIDString):
                  raise NoSuchPluginErrror(pluginIDString)
            return self.registry[pluginIDString]


      def getRouteExtension(self, pluginIDString):
            if not self.registry.get(pluginIDString):
                  raise NoSuchPluginError(pluginIDString)
            return self._slots[pluginIDString].routeExtension



      def readRouteVars(self, request, pluginIDString):
            if not self.registry.get(pluginIDString):
                  raise NoSuchPluginError(pluginIDString)

            ext = self.getRouteExtension(pluginIDString)
            path = request.path
            pathElements = path.split('/')

            result = {}
            for e in ext.elements:
                  if not e.isStatic():
                        result[e.elementString] = pathElements[e.positionIndex]

            return result


      # for testing at the command line when an HTTP request is unavailable
      def testReadRouteVars(self, path, pluginIDString):
            if not self.registry.get(pluginIDString):
                  raise NoSuchPluginError(pluginIDString)

            ext = self.getRouteExtension(pluginIDString)
            #path = request.path
            pathElements = path.split('/')

            result = {}
            for e in ext.elements:
                  if not e.isStatic():
                        result[e.elementString] = pathElements[e.positionIndex]

            return result
                  
                              
      def getSlots(self):
            return self._slots.values()
      
      slots = property(getSlots)
      

            

