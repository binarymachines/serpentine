"""Initialization logic for Serpentine network application stack.


"""

import os
import logging
import yaml

from jinja2 import StrictUndefined
from content import *
from db import *
from events import *
from core import *
from reporting import *

from sqlalchemy.orm import mapper
from sqlalchemy.exc import SQLAlchemyError

logging.basicConfig( filename = 'bifrost.log', level = logging.INFO, format = "%(asctime)s - %(message)s" )
log = logging.info



class Properties( object ):
      def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

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


class Environment():
      def __init__(self):
            self.appName = None
            self.appVersion = None
            self.config = None
            self.contentRegistry = ContentRegistry()
            self.templatePath = None
            self.outputPath = None
            self.stylesheetPath = None
            self.classLoader = ClassLoader()
            self.templateManager = None
            self.persistenceManager = None
            self.persistenceManagerMap = {}
            self.displayManager = None
            self.frontController = None
            self.reportManager = None
            self.responderMap = {}
            self.urlBase = None
      
            self.__controllerRegistry = {}
      
      def bootstrap(self, initFileName):
            """Find and read an initialization file for startup.
            bootstrap() looks for a config file named <initFileName> 
            in its current location.
            """

            try:
                  f = open(initFileName)
                  config = yaml.load(f.read())
                  log('Opened config file, reading settings...')

                  self.appName = config['global']['app_name']
                  self.appVersion = config['global']['app_version']

                  self.urlBase = config['global']['url_base']
                  self.outputPath = os.path.join(config['global']['app_root'], config['global']['output_file_path'])
                  self.reportPath = os.path.join(config['global']['app_root'], config['global']['report_file_path'])
                  self.staticFilePath = os.path.join(config['global']['app_root'], config['global']['static_file_path'])
                  self.templatePath = os.path.join(config['global']['app_root'], 
                                                   config['content_registry']['template_path'])
                  j2Environment = jinja2.Environment(loader = jinja2.FileSystemLoader(self.templatePath), 
                                                    undefined = StrictUndefined, cache_size=0)
                  self.templateManager = JinjaTemplateManager(j2Environment)

                  self.stylesheetPath = os.path.join(config['global']['app_root'], 
                                                     config['display_manager']['stylesheet_path'])

                  self.reportManager = ReportManager(self.reportPath)
                  
                  
                  self.config = config
                  return self

            except IOError, err:
                  log('Error opening config file: %s' % err.message)
                  raise err
            except KeyError, err:
                  log('Error reading config file: %s' % err.message)
                  raise err
            finally:
                  pass
      

      def initializeReporting(self):
            packageName = self.config['global']['default_report_package']

            if not self.config['reports']:
                  return

            for reportName in self.config['reports']:  
            
                dataSourceClassName = self.config['reports'][reportName]['data_source']
                fqSourceClassName = '.'.join([packageName, dataSourceClassName])
                dataSourceClass = self.classLoader.loadClass(fqSourceClassName)
                dataSource = dataSourceClass()
                
                generatorClassName = self.config['reports'][reportName]['generator']
                
                # first try to load one of the built-in generators
                generatorClass = None
                fqGeneratorClassName = '.'.join(['reporting', generatorClassName])
                
                try:
                    generatorClass = self.classLoader.loadClass(fqGeneratorClassName)
                except ClassLoaderError, err:
                    # if we don't find it, look for a user-defined one in the
                    # declared reporting package                
                    fqGeneratorClassName = '.'.join([packageName, generatorClassName])
                    # if this fails, let the resulting exception propagate
                    generatorClass = self.classLoader.loadClass(fqGeneratorClassName)
                    
                generator = generatorClass()
                
                formClassName = self.config['reports'][reportName]['form']
                fqFormClassName = '.'.join([packageName, formClassName])
                formClass = self.classLoader.loadClass(fqFormClassName)
                form = formClass()
                
                report = Report(dataSource, generator, form)
                self.reportManager.registerReport(reportName, report)
                

      def getHelperFunctions(self):
            """Return all registered helper functions across all content frames
            """

            helpers = []
            if self.contentRegistry is not None:
                  for frameID in self.contentRegistry.frames:
                        helper = self.contentRegistry.getHelperFunctionForFrame(frameID)
                        if helper is not None:
                              helpers.append(helper)

            return helpers
                        

      def loadResponders(self):                    
            if 'responders' in self.config:
                  for className in self.config['responders']:
                        packageName = self.config['global']['default_responder_package']
                        fqClassName = '.'.join([packageName, className])
                        responderClass = self.classLoader.loadClass(fqClassName)
                        responder = responderClass()
                        responder.type = self.config['responders'][className]['type']

                        if responder.type == 'xml' or responder.type == 'html' and 'template' in self.config['responders'][className]:
                             templateName = self.config['responders'][className]['template']
                             responder.template = self.templateManager.getTemplate(templateName)


                        responderAlias = self.config['responders'][className]['alias']
                        self.responderMap[responderAlias] = responder
      
      def _createFrame(self, templateObject):
            if templateObject.filename.endswith('html') or templateObject.filename.endswith('tpl'):
                  return HTMLFrame(templateObject)
            elif templateObject.filename.endswith('xml'):
                  return XMLFrame(templateObject)
            

      def populateContentRegistry(self):
            creg = self.contentRegistry
            for frameID in self.config['content_registry']['frames']:

                  templateName = self.config['content_registry']['frames'][frameID]['template'] # the underlying filename
                  templateObject = self.templateManager.getTemplate(templateName)
                  
                  
                  
                  frameObject = self._createFrame(templateObject)

                  if frameObject is None:
                        raise Exception("Somehow created a NULL Frame.")

                  form = self.config['content_registry']['frames'][frameID].get('form')
                  if form is not None:
                        formPkg = self.config['global']['default_form_package']
                        fqFormClassname = formPkg + '.'
                        fqFormClassname = fqFormClassname + form
                        formClass = self.classLoader.loadClass(fqFormClassname)
                        
                        creg.addFrame(frameObject, frameID, formClass)
                  else:
                        creg.addFrame(frameObject, frameID)

                  helperFunctionName = self.config['content_registry']['frames'][frameID].get('helper')
                  if helperFunctionName is not None:
                        # We can load a function just like a class
                        helperPkg = self.config['global']['default_helper_package']
                        fqFunctionName = '.'.join([helperPkg, helperFunctionName])
                        helperFunction = self.classLoader.loadClass(fqFunctionName)  # not a "class" really, but so what?
                        creg.setHelperFunctionForFrame(frameID, helperFunction)

            # self-documenting features
            # users do not need to explicitly register the documentation frames,
            # which have designated names
            # 
            apiTemplateName = self.config['global']['api_frame']            
            apiTemplateObject = self.templateManager.getTemplate(apiTemplateName)
            apiFrameObject = self._createFrame(apiTemplateObject)
            
            controllerTemplateName = self.config['global']['controller_frame']
            controllerTemplateObject = self.templateManager.getTemplate(controllerTemplateName)
            controllerFrameObject = self._createFrame(controllerTemplateObject)

            responderTemplateName = self.config['global']['responder_frame']
            responderTemplateObject = self.templateManager.getTemplate(responderTemplateName)
            responderFrameObject = self._createFrame(responderTemplateObject)

            creg.addFrame(apiFrameObject, 'api')
            creg.addFrame(controllerFrameObject, 'controller')
            creg.addFrame(responderFrameObject, 'responder')


      def mapFramesToViews(self):
            viewManager = ViewManager(self.contentRegistry)
            for controllerID in self.config['view_manager']['controllers']:
                  if controllerID not in self.__controllerRegistry:
                        raise ConfigError("No controller has been registered under alias '%s'; cannot assign to a frame." % controllerID)

                  frameSet =  self.config['view_manager']['controllers'][controllerID]
                  for record in frameSet:
                        viewManager.mapFrameID(record['frame'], controllerID, record['method'])
            
            self.viewManager = viewManager
            return viewManager
            
      def assignStylesheetsToXMLFrames(self):            
            displayManager = DisplayManager(self.stylesheetPath)
            if self.config['display_manager']['frames'] is not None:
                  for frameID in self.config['display_manager']['frames']:
                        stylesheet = self.config['display_manager']['frames'][frameID]['stylesheet']
                        displayManager.assignStylesheet(stylesheet, frameID)

            self.displayManager = displayManager
            return displayManager


      def initializeDataStore(self):
            startupDBName = self.config['global']['startup_db']
            if startupDBName not in self.config['databases']:
                  raise ConfigError(
                        "Startup database alias '%s' is not in the list of databases. Please check your config file." % startupDBName)

            
            dbType = self.config['databases'][startupDBName]['type']
            schema = self.config['databases'][startupDBName]['schema']
            username = self.config['databases'][startupDBName]['username']
            password = self.config['databases'][startupDBName]['password']
            host = self.config['databases'][startupDBName]['host']

            # right now we only do MySQL; later on we'll add a Factory
            database = MySQLDatabase(host, schema)
            database.login(username, password)
            persistenceManager = PersistenceManager(database)
            self.persistenceManagerMap[startupDBName] = persistenceManager 
            
            self.persistenceManager = self.persistenceManagerMap[startupDBName]
            return self.persistenceManager

      def mapModelsToDatabase(self):
            # TODO: add logic to extract model aliases from the config if they've been provided

            leafModels = []
            for model in self.config['models']:
                  # "peer" models represent a one-to-one relationship
                  #
                  peerModels = self.config['models'][model].get('peers')
                  if peerModels is not None:
                        fqModelType = '.'.join([self.config['global']['default_model_package'], model])
                        peerModelArray = peerModels.split(',')
                        for item in peerModelArray:
                              peer = item.strip()
                              fqPeerModelType = '.'.join([self.config['global']['default_model_package'], peer])
                              tableName = self.config['models'][model]['table']
                              peerTableName = self.config['models'][peer]['table']
                              self.persistenceManager.mapPeerToPeer(fqModelType,
                                                                    tableName,
                                                                    ''.join([model[0:1].lower(), model[1:]]),
                                                                    fqPeerModelType,
                                                                    peerTableName,
                                                                    ''.join([peer[0:1].lower(), peer[1:]]), 
                                                                    model_alias=model, 
                                                                    peer_model_alias=peer)
                                                           
                  
                  # "child" models represent a one-to-many relation
                  #
                  childModels = self.config['models'][model].get('children')
                  if childModels is None:
                        leafModels.append(model)
                        fqModelType = '.'.join([self.config['global']['default_model_package'], model])
                        self.persistenceManager.mapTypeToTable(fqModelType, self.config['models'][model]['table'], model_alias=model)
                  else:
                        fqParentModelType = '.'.join([self.config['global']['default_model_package'], model]) 
                        childModelArray = childModels.split(',')
                        for item in childModelArray:
                              child = item.strip()
                              fqChildModelType = '.'.join([self.config['global']['default_model_package'], child])

                              parentTableName = self.config['models'][model]['table']
                              childTableName = self.config['models'][child]['table']
                              self.persistenceManager.mapParentToChild(fqParentModelType, 
                                                                        parentTableName, 
                                                                       ''.join([model[0:1].lower(), model[1:]]),
                                                                       fqChildModelType,
                                                                       childTableName,
                                                                       ''.join([child[0:1].lower(), child[1:]]), 
                                                                       parent_model_alias=model, 
                                                                       child_model_alias=child)
            
            

      def initializeEventDispatcher(self):
            dispatcher = EventDispatcher()
            self.eventDispatcher = dispatcher
            return dispatcher

      def assignControllers(self):
            frontController = FrontController()
            for className in self.config['controllers']:
                  packageName = self.config['global']['default_controller_package']

                  # construct a fully qualified (fq...) class name from global settings
                  fqClassName = '.'.join([packageName, className])
                  controllerClass = self.classLoader.loadClass(fqClassName)

                  # now get the alias
                  attributes = self.config['controllers'][className]
                  alias = attributes['alias']
                  modelName = alias 
                  if attributes.get('model') != None:
                      modelName = attributes['model']
                  
                  # determine this Controller's Model class
                  fqModelClassName = '.'.join([self.config['global']['default_model_package'], modelName])
                  modelClass = self.classLoader.loadClass(fqModelClassName)

                  # now get the Form class if there is one
                  formClass = None
                  formClassName = ''.join([modelName, 'Form']) 
                  if attributes.get('form_class') != None:
                      formClassName = attributes['form_class']
                      fqFormClassName = '.'.join([self.config['global']['default_forms_package'], formClassName])                  
                      formClass = self.classLoader.loadClass(fqFormClassName)

                  controllerInstance = None
                  
                  #
                  # Controllers should either be descended from BaseController -- in which case
                  # they should take the model and form classes as constructor params -- or not, 
                  # in which case they need only need to take the model instance.
                  # 
                  # TODO: eliminate this logic; all controllers will take a Model instance
                  if issubclass(controllerClass, BaseController): 
                        controllerInstance = controllerClass(modelClass)
                  else:
                        controllerInstance = controllerClass(modelClass())

                  frontController.assignController(controllerInstance, alias)
                  
                  # not used externally; this is for error checking ViewManager entries elsewhere in the config
                  self.__controllerRegistry[alias] = controllerInstance

            self.frontController = frontController
            return frontController
