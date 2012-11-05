"""Plugin for run-once Netpath initialization code


"""

import inspect
from environment import *
from reporting import *


class NetPathStartupPlugin(object):
      """This plugin passes an instance of a NetPath Environment object 
      to any route callbacks that accept a 'environment' keyword argument.
      For Serpentine apps, that's all of them. This is necessary in order
      to ensure that heavyweight init routines, such as those acquiring
      database connections, only occur once per session 
      rather than once per-request.
      """

      name='NetPathEnvironment'

      def __init__(self, initFileName):
            environment = Environment().bootstrap(initFileName)
            
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
            
            self.environment = environment
            self.keyword = 'environment'

     

      def setup(self, app):
            """Make sure that other installed plugins don't have the same
            keyword argument.
            """
            for other in app.plugins:
                if not isinstance(other, NetPathStartupPlugin): 
                      continue
                if other.keyword == self.keyword:
                        raise PluginError("Found another plugin with "\
                        "conflicting settings (non-unique keyword).")

      def apply(self, callback, context):
            conf = context['config'].get(self.name) or {}
            keyword = conf.get('keyword', self.keyword)
            args = inspect.getargspec(context['callback'])[0]
            if keyword not in args:
                  return callback

            def wrapper(*args, **kwargs):                                  
                  kwargs[keyword] = self.environment
                  rv = callback(*args, **kwargs)
                  return rv

            return wrapper

            
   
