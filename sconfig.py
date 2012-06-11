#!/usr/bin/python

import os, sys
import db
import time
import curses, traceback
import curses.wrapper
from StringIO import StringIO

import jinja2

from wtforms import *
from lxml import etree
from sqlalchemy import *

from cli import *
from content import *


class NoSuchFieldSpecError(Exception):
    def __init__(self, name):
        Exception.__init__(self, "No FieldSpec named %s in this FormSpec." % name)


class ControllerMethodConfig:
    def __init__(self, controllerMethodName, frameAlias):        
        self.name = controllerMethodName
        self.frame = frameAlias


class ControllerConfig:
    def __init__(self, className, alias, modelClassName):
        self.name = className
        self.alias = alias
        self.model = modelClassName
        self.methods = []
        
    def addMethod(self, controllerMethodConfig):
        self.methods.append(controllerMethodConfig)


class DatabaseConfig:
    def __init__(self, host, schema, username, password):
        self.type = "mysql"
        self.host = host
        self.schema = schema
        self.username = username
        self.password = password




class FrameConfig:
    def __init__(self, name, template, formClassName, frameType, helperName = None):
        self.name = name
        self.template = template
        self.form = formClassName
        self.type = frameType
        self.helper = helperName


class ModelConfig(object):
    def __init__(self, name, tableName, children = None):
        self.name = name
        self.table = tableName
        if children is None:
            self._children  = []
        else:
            self._children = children

    def addChild(self, modelConfigName):
        self._children.append(modelConfigName)

    def getChildren(self):
        """Return the child model list as a comma-separated string"""
        if len(self._children) == 0:
            return ""
        else:
            return ", ".join(self._children)

    children = property(getChildren)


class SConfigurator(object):
      def __init__(self):
            self.app_name = None
            self.app_root = None
            self.app_version = '1.0'
            self.web_app_name = None
            self.hostname = None
            self.port = None
            self.static_file_path = None
            self.default_form_package = None
            self.default_model_package = None
            self.default_controller_package = None
            self.default_helper_package = None
            self.default_reporting_package = None
            self.default_responder_package = None
            self.startup_db = None
            self.url_base = None
            self.template_path = None
            self.stylesheet_path = None
            self.dependency_path = None
            self.config_filename = None

            self.models = {}
            self.datasources = {}
            self.controls = {}
            self.frames = {}
            self.controllers = {}
            self.xmlFrames = {}
            self.views = {}
            self.databases = {}

            self.responders = {}
            self.helpers = {}
            self.dependencies = {}
                                


      def convertTableNameToModelName(self, tableName):
          """Convert an underscore-style db table name to a camel-cased class name."""

          # plural to singular
          tempName = tableName
          if tableName[len(tableName)-1] == 's':
              tempName = tableName[0: len(tableName)-1]

          # remove the underscore separator and camel-case any compound names
          underscoreIndex = tempName.find('_')
          if underscoreIndex != -1:
              pieces = [tempName[0: underscoreIndex].capitalize(), tempName[underscoreIndex+1:].capitalize()]
              className = ''.join(pieces)
          else:       
              className = tempName.capitalize()

          return className


      def run(self, screen):
          self.setupGlobalData(screen)
          self.setupDatabases(screen)

          tableList = self.selectTables(screen)
          # TODO: Add parent-child mapping selection logic
          modelTableMap = self.createModelTableMap(tableList)

          self.setupDatasources(screen)
          self.setupControls(screen)
          self.setupWSGI(screen)

          currentDir = os.getcwd()
          bootstrapDir = os.path.join(currentDir, "bootstrap")
          env = jinja2.Environment(loader = jinja2.FileSystemLoader(bootstrapDir))
          templateMgr = JinjaTemplateManager(env)

          self.generateModelCode(modelTableMap.keys())
          formSpecArray = self.createFormSpecs(modelTableMap)

          # some frames will have helper functions
          self.designateHelperFunctions(formSpecArray, screen)

          self.generateControllerCode(formSpecArray, templateMgr)
          self.generateApplicationTemplates(formSpecArray, templateMgr)
          self.generateFormCode(formSpecArray, templateMgr)
          self.generateShellScripts(templateMgr)
          

          # now generate the config file

          configFile = None
          try:
              configFileTemplate = templateMgr.getTemplate('config_template.tpl')
              configFilename = '%s.conf' % self.projectName.lower()
              configFile = open(os.path.join('bootstrap', configFilename), 'w')
              configFile.write(configFileTemplate.render(config = self))
              #configFile.close()
              
              wsgiFile = open(os.path.join('bootstrap', '%s.wsgi' % self.web_app_name), 'w')
              wsgiFileTemplate = templateMgr.getTemplate("wsgi_file.tpl")
              wsgiData = wsgiFileTemplate.render(config = self)
              wsgiFile.write(wsgiData)
              #wsgiFile.close()

              wsgiVHostEntryFile = open(os.path.join('bootstrap', '%s_vhost_entry.xml' % self.web_app_name), 'w')
              wsgiVHostTemplate = templateMgr.getTemplate('wsgi_vhost_entry.tpl')
              wsgiVHostData = wsgiVHostTemplate.render(config = self)
              wsgiVHostEntryFile.write(wsgiVHostData)
              #wsgiVHostEntryFile.close()

              self.config_filename = configFilename
          finally:
              if configFile is not None:
                  configFile.close()

              if wsgiFile is not None:
                  wsgiFile.close()

              if wsgiVHostEntryFile is not None:
                  wsgiVHostEntryFile.close()

              
      
      def designateHelperFunctions(self, formSpecs, screen):
          """Allow the user to specify a helper function for one or more frames"""

          pass


      def _addLookupTable(self, lookupTableArray, screen):
          screen.clear()
          tablesToAdd = self.selectTables(screen)
          tableNames = [table.name for table in tablesToAdd]
          result = lookupTableArray
          result.extend(tableNames)
          return result


      def _removeLookupTable(self, lookupTableArray, screen):
          screen.clear()
          multiChoicePrompt = MultipleChoiceMenuPrompt(lookupTableArray, 'Select one or more tables to remove from the list.')
          while not multiChoicePrompt.escaped:
              tablesToRemove = multiChoicePrompt.show(screen)
              
          Notice('Removing tables %s from lookups.' % tableList).show()
          result = [item for item in lookupTableArray if item not in tablesToRemove]
          return result


      def setupControls(self, screen):
          """Set up zero or more UI controls, to be rendered via templates and supplied with data
          via datasources
          """
          screen.clear()
          choices = { 'y': True, 'n': False }
          prompt = TextSelectPrompt('Auto-create HTML select controls from lookup tables?', choices, 'y')          
          selection = prompt.show(screen)

          if selection:
              Notice('OK. Lookup tables will be inferred from their names.').show(screen)
              Notice('Compiling list..').show(screen)

              targetDBConfig = self.databases[self.startup_db]
              dbInstance = db.MySQLDatabase(targetDBConfig.host, targetDBConfig.schema)
              dbInstance.login(targetDBConfig.username, targetDBConfig.password)

              tableList = dbInstance.listTables()          
              lookupTables = [table for table in tableList if table[0:7] == 'lookup_']
                        
              actionMenu = Menu(['Add Lookup Table', 'Show Lookup Tables', 'Remove Lookup Table', 'Clear Lookup Tables'])
              actionPrompt = MenuPrompt(actionMenu, 'Select an action to manage lookup tables.')
              
              while not actionPrompt.escaped:
                  
                  displayList = '\n'.join(lookupTables)                  
                  selection = actionPrompt.show(screen)
                  index = actionPrompt.selectedIndex

                  if index == 1: # add 
                      lookupTables = self._addLookupTable(lookupTables, screen)
              
                  elif index == 2: # show
                      Notice(displayList).show(screen)
                      Notice('Hit any key to continue.').show(screen)
                      screen.getch()

                  elif index == 3:  # remove
                      lookupTables = self._removeLookupTable(lookupTables, screen)
                      
                  elif index == 4: # clear the list
                      lookupTables = []
                  
                  
                  screen.clear()


              for tableName in lookupTables:
                  parameterSet = []
                  parameterSet.append(DataSourceParameter('table', tableName))
                  parameterSet.append(DataSourceParameter('name_field', 'name'))
                  parameterSet.append(DataSourceParameter('value_field', 'id'))
                  sourceName = '%s_src' % tableName
                  self.datasources[sourceName] = DataSourceSpec('menu', parameterSet)
                  
                  controlName = '%s_select' % tableName
                  self.controls[controlName] = ControlSpec('select', controlName, sourceName)
              
    
      def addSelectControl(self, screen):
          pass


      def addRadioControl(self, screen):
          pass


      def addTableControl(self, screen):
          pass


      def setupDatasources(self, screen):
          """Specify zero or more data 'adapters' to populate UI controls & other data-driven types"""

          results = {}

          options = ['Create new data source', 'List data sources']
          
          
          prompt = MenuPrompt(Menu(options), 'Select an option from the menu.')
          screen.clear()

          Notice('Create one or more datasources to populate UI controls.').show(screen)
          while not prompt.escaped:
              selection = prompt.show(screen)
              if prompt.escaped:
                  break
              if prompt.selectedIndex == 1: # create datasource
                  sourceNamePrompt = TextPrompt('Enter a name for the datasource:')
                  sourceName = sourceNamePrompt.show(screen)
                  
                  sourceTypeOptions = ['menu', 'grid']
                  sourceTypePrompt = MenuPrompt(Menu(sourceTypeOptions), 'Select a datasource type.')
                  sourceType = sourceTypePrompt.show(screen)
                  
                  sourceParams = []

                  table = self.selectSingleTable(screen, 'Select the target table for the datasource.')
                  screen.clear()
                  sourceParams.append(DataSourceParameter('table', table.name))
                  
                  if sourceType == 'menu':
                      # prompt for the name and value fields (usually the 'name' and 'id' columns)
                      Notice('Table "%s" selected. Select source fields next.' % table.name)
                      columnNames = [column.name for column in table.columns]                      
                      columnMenu = Menu(columnNames)
                      valueFieldPrompt = MenuPrompt(columnMenu, 'Select the value field (usually the primary key field).')
                      valueField = valueFieldPrompt.show(screen)
                      nameFieldPrompt = MenuPrompt(columnMenu, 'Select the name field (the value displayed in menus or other controls.')
                      nameField = nameFieldPrompt.show(screen)
                      
                      sourceParams.append(DataSourceParameter('name_field', nameField))
                      sourceParams.append(DataSourceParameter('value_field', valueField))

                  if sourceType == 'grid':
                      fieldListPrompt = MultipleChoiceMenuPrompt(columnNames, 'Select one or more columns from the source table.')
                      selectedFields = fieldListPrompt.show(screen)
                      sourceParams.append(DataSourceParameter('fields', ','.join(selectedFields)))
                      

                  newSpec = DataSourceSpec(sourceType, sourceParams)
                  self.datasources[sourceName] = newSpec

              if prompt.selectedIndex == 2:     # list existing sources
                  screen.addstr("\nDatasources: " + ", ".join(self.datasources.keys()) + "\nHit any key to continue.")
                  screen.getch()

              screen.clear()

          


      def setupDatabases(self, screen):
          """Allow the user to specify one or more named database instances from which to select later"""

          options = ["Create new database", "List databases"]

          prompt = MenuPrompt(Menu(options), "Select an option from the menu.")
          screen.clear()
          Notice('Set up one or more database instances to connect to from the web application.').show(screen)
          while not prompt.escaped:
              selection = prompt.show(screen)
              if prompt.escaped:
                  break
              if prompt.selectedIndex == 1:
                  schema = TextPrompt("Enter database schema", self.web_app_name).show(screen)
                  username = TextPrompt("Enter database username", None).show(screen)
                  password = TextPrompt("Enter database password", None).show(screen)
                  dbName = TextPrompt("Enter a name for this database instance", "localhost.%s" % schema).show(screen)
                  
                  self.databases[dbName] = DatabaseConfig("localhost", schema, username, password)
                  screen.addstr("\n New database created. Hit any key to continue.")
                  screen.getch()
                  screen.clear()
              if prompt.selectedIndex == 2:
                  screen.addstr("\nDatabases: " + ", ".join(self.databases.keys()) + "\nHit any key to continue.")
                  screen.getch()
                  screen.clear()
              

      def setupGlobalData(self, screen):
            """Set project values which will be used by various sections of the configuration.

            Here is where we set the project name, basic path information, and packages names for generated MVC classes.

            Arguments:
            screen -- curses display context
            """

            screen.clear()
            Notice('Welcome to SConfigurator, the Serpentine auto-config utility.').show(screen)
            Notice('Set basic project information for the web app.').show(screen)

            projectNamePrompt = TextPrompt("Enter project name", None)
            self.projectName = projectNamePrompt.show(screen)
            self.app_name = self.projectName
            self.web_app_name = self.projectName.lower()
            self.url_base = self.projectName.lower()

            currentDir = os.getcwd()
            self.app_root = currentDir

            self.dependency_path = os.path.join(self.app_root, "bootstrap", "dependencies")
            

            # this is a standalone global in the config, so it must be an absolute path
            self.static_file_path = os.path.join(self.app_root, "templates") 

            # these are local to their respective sections in the config, so they are relative paths
            self.template_path = "templates"
            self.stylesheet_path = "stylesheets"
            
            scriptPath = [self.static_file_path, 'scripts']
            stylesPath = [self.static_file_path, 'styles']
            xmlPath = [self.static_file_path, 'xml']
                       
            self.default_form_package = '%s_forms' % self.projectName.lower()
            self.default_model_package = '%s_models' % self.projectName.lower()
            self.default_controller_package = '%s_controllers' % self.projectName.lower()
            self.default_helper_package = '%s_helpers' % self.projectName.lower()
            
            try:
                if not os.path.exists(self.static_file_path):
                    os.system('mkdir %s' % self.static_file_path) 
                
                if not os.path.exists(self.stylesheet_path):
                    os.system('mkdir %s' % self.stylesheet_path)

                if not os.path.exists(os.path.join(scriptPath[0], scriptPath[1])):
                    os.system('mkdir %s' % os.path.join(scriptPath[0], scriptPath[1]))

                if not os.path.exists(os.path.join(stylesPath[0], stylesPath[1])):
                    os.system('mkdir %s' % os.path.join(stylesPath[0], stylesPath[1]))

                if not os.path.exists( os.path.join(xmlPath[0], xmlPath[1])):
                    os.system('mkdir %s' % os.path.join(xmlPath[0], xmlPath[1]))

            except IOError, err:
                raise err

            self.globalDataInitialized = True
            

      def selectSingleTable(self, screen, screenMsg = None):
          
          screen.clear()
          if screenMsg:
              Notice(screenMsg).show(screen)

          dbName = MenuPrompt(Menu(self.databases.keys()), "Select a DB instance to connect to.").show(screen)
          dbConfig = self.databases[dbName]
          self.startup_db = dbName

          selectedTable = None

          try:
              # first connect to the DB
                
              dbInstance = db.MySQLDatabase(dbConfig.host, dbConfig.schema)
              dbInstance.login(dbConfig.username, dbConfig.password)
                
              # get a listing of all tables and present in menu form
              m = Menu(dbInstance.listTables())
              prompt = MenuPrompt(m, 'Select a database table.')
              tableName = prompt.show(screen)                                                   
              selectedTable = dbInstance.getTable(tableName)          
              return selectedTable

          finally:
              pass


      def selectTables(self, screen):
            screen.clear()
            dbName = MenuPrompt(Menu(self.databases.keys()), "Select a DB instance to connect to.").show(screen)
            dbConfig = self.databases[dbName]
            self.startup_db = dbName

            selectedTables = []

            try:
                # first connect to the DB
                
                dbInstance = db.MySQLDatabase(dbConfig.host, dbConfig.schema)
                dbInstance.login(dbConfig.username, dbConfig.password)
                
                # get a listing of all tables and present in menu form
                m = Menu(dbInstance.listTables())
                prompt = MultipleChoiceMenuPrompt(m, 'Select one or more database tables to add.')
                selectedTableNames = prompt.show(screen)

                for name in selectedTableNames:                                        
                    selectedTables.append(dbInstance.getTable(name))
            
                return selectedTables
            finally:
                pass


      def createModelTableMap(self, selectedTables):
          """ use the names of the selected tables to generate camel-cased class names.

          Arguments:
          selectedTables -- an array of SQLAlchemy Table objects reflected from the current DB schema
          screen -- the curses graphical context object
          """

          modelTableMap = {}
          for table in selectedTables:
              modelName = self.convertTableNameToModelName(table.name)
              modelTableMap[modelName] = table              
              self.models[modelName] = ModelConfig(modelName, table.name, None)

          # for now, accept all generated model names. TODO: eventually allow changes.
         
          return modelTableMap
         

      def generateModelCode(self, modelNames):
          """Generate all boilerplate Model classes, in a single module

          Arguments: 
          modelNames -- an array of model names
          """     
          modelPkg = os.path.join("bootstrap", "%s.py" % self.default_model_package) 
          f = open(modelPkg, "a")
          #f.write("#!/usr/bin/python\n\n")
          for modelName in modelNames:
              f.write("\nclass %s(object): pass" % modelName)
              f.write("\n\n")
          f.close()

      def createFormSpecs(self, modelTableMap):
          """For each model name in the dictionary, generate form specification (FormSpec) object.

          Arguments:
          modelTableMap -- a dictionary of table objects in our schema, indexed by model classnames. 
                           The expression modelTableMap['Widget'] would yield the SQLAlchemy Table object 
                           corresponding to "widgets" in the database.
          
          Returns:
          an array of FormSpec instances
          """

          formSpecs = []

          try:        
              factory = FieldSpecFactory()
              for modelName in modelTableMap:                  
                  # formspecs need the URL base to properly generate action URLs in the HTML templates
                  newFormSpec = FormSpec(modelName, self.url_base) 
                  table = modelTableMap[modelName]
                  for column in table.columns:
                      newFormSpec.addField(factory.create(column))

                  formSpecs.append(newFormSpec)
                  
              return formSpecs
          finally:
              pass
      
          
      def setupWSGI(self, screen):
          """Get the settings for the app's interface with Apache

          Arguments:
          screen -- display target for menus and prompts
          """
          screen.clear()
          Notice('Enter WSGI config information.').show(screen)
          hostPrompt = TextPrompt('Enter the hostname for this app: ', 'localhost')
          self.hostname = hostPrompt.show(screen)

          portPrompt = TextPrompt('Enter HTTP port for this app: ', '80')
          self.port = portPrompt.show(screen)
          
          
      def generateShellScripts(self, templateManager):
          """Generate the shell scripts to be used for post-config setup
          
          templateManager -- repository holding refs to all our file templates
          """

          scriptFile = None

          try:
              scriptTemplate = templateManager.getTemplate('setup_content_refs.tpl')
              scriptData = scriptTemplate.render(config = self)
              scriptFilename = os.path.join('bootstrap', 'setup_content_refs.sh')
              scriptFile = open(scriptFilename, 'w')
              scriptFile.write(scriptData)
              result = subprocess.call(['chmod', 'u+x', scriptFilename])
          finally:
              if scriptFile:
                  scriptFile.close()
          
          

      def generateFormCode(self, formSpecs, templateManager):
          """Create the WTForms Form instances for the application under construction

          Arguments:
          formSpecs -- an array of FormSpec instances
          templateManager -- repository holding refs to all our file templates
          """

          formPkgTemplate = templateManager.getTemplate("forms_package.tpl")
          formPkgString = formPkgTemplate.render(formspecs = formSpecs)
          
          # write the package string out to a file
          formPkgName = os.path.join("bootstrap", "%s_forms.py" % self.projectName.lower())
          formPkgFile = open(formPkgName, "w")
          formPkgFile.write(formPkgString)
          formPkgFile.close()


      def generateControllerCode(self, formSpecs, templateManager):
          """Generate Python package specifying the app's controller classes"""

          controllerPkgFile = None

          try:
              for fSpec in formSpecs:
                  controllerClassName = "%sController" % fSpec.model
                  controllerAlias = fSpec.model
                  modelClassName = fSpec.model
                  self.controllers[controllerAlias] = ControllerConfig(controllerClassName, controllerAlias, modelClassName)

              controllerPkgTemplate = templateManager.getTemplate("controllers_package.tpl")
              controllerPkgString = controllerPkgTemplate.render(config = self)

              controllerPkgName = os.path.join("bootstrap", "%s_controllers.py" % self.projectName.lower())

              controllerPkgFile = open(controllerPkgName, "w")
              controllerPkgFile.write(controllerPkgString)
              controllerPkgFile.close()
          finally:
              if controllerPkgFile is not None:
                  controllerPkgFile.close()


      def generateApplicationTemplates(self, formSpecs, templateManager):
          """Create the master template files for the application under construction"""

          xmlHandle = None
          xmlTemplate = templateManager.getTemplate("formspec_xml.tpl")
          xmlFile = None
          htmlFile = None
          baseTemplateFile = None

          generatedFiles = {}

          try:
              # First render the base HTML template from which our other templates will inherit
              #
              baseTemplate = templateManager.getTemplate('base_html_template.tpl')
              baseTemplateData = baseTemplate.render(config = self)
              baseTemplateFilename = os.path.join('bootstrap', 'base_template.html')
              baseTemplateFile = open(baseTemplateFilename, 'w')
              baseTemplateFile.write(baseTemplateData)
              baseTemplateFile.close()

               # transform the XML seed template into a FormSpec XML document.
              for fSpec in formSpecs:
                  
                  # Use each FormSpec object in our list to populate the model XML template
                  # and create an XML representation of the FormSpec.
                  #
                  #xmlHandle = StringIO(xmlTemplate.render(formspec=fSpec))
                  xmlString = xmlTemplate.render(formspec = fSpec)

                  # the raw xml text now resides in the file-like string object xmlHandle

                  # write it to a file with the same name as the underlying Model; 
                  # i.e., for the Widget formspec the file would be Widget.xml
                  #
                  xmlFilename = os.path.join("bootstrap", "%s.xml" % fSpec.model.lower())
                  xmlFile = open(xmlFilename, "w") 
                  xmlFile.write(xmlString)
                  xmlFile.close()

                  # Next, transform the FormSpec document into a set of final HTML templates.
                  # The resulting templates will become views in the live application.
                  #
                  # index template, for viewing all objects of a given type

                  xslFilename = os.path.join("bootstrap", "index_template.xsl")
                  xslFile = open(xslFilename)
                  xslTree = etree.parse(xslFile)
                  indexTemplateTransform = etree.XSLT(xslTree)

                  xmlFile = open(xmlFilename, 'r')
                  # create a DOM tree
                  formSpecXML = etree.parse(xmlFile)
                  

                  indexTemplateHTMLDoc = indexTemplateTransform(formSpecXML)
                  
                  indexFilename = os.path.join("bootstrap", "%s_index.html" % fSpec.model.lower())
                  indexFrameFileRef = "%s_index.html" % fSpec.model.lower()
                  htmlFile = open(indexFilename, "w")   
                  #htmlFile.write(etree.tostring(indexTemplateHTMLDoc, pretty_print=True))
                  htmlFile.write(indexTemplateHTMLDoc.__str__())
                  htmlFile.close()
                  xmlFile.close()
                  indexFrameAlias = "%s_index" % fSpec.model.lower()
                  
                  self.frames[indexFrameAlias] = FrameConfig(indexFrameAlias, indexFrameFileRef, fSpec.formClassName, "html")
                  
                  for controllerAlias in self.controllers:
                      if self.controllers[controllerAlias].model == fSpec.model:
                          self.controllers[controllerAlias].addMethod(ControllerMethodConfig("index", indexFrameAlias))

                  # 
                  # insert template: creates a form for adding 
                  # a single object
                  
                  xslFilename = os.path.join("bootstrap", "insert_template.xsl")
                  xslTree = etree.parse(xslFilename)
                  insertTemplateTransform = etree.XSLT(xslTree)
                  insertHTMLDoc = insertTemplateTransform(formSpecXML)

                  insertFilename = os.path.join("bootstrap", "%s_insert.html" % fSpec.model.lower())
                  insertFrameFileRef = "%s_insert.html" % fSpec.model.lower()
                  htmlFile = open(insertFilename, "w")  
                  htmlFile.write(insertHTMLDoc.__str__())
                  htmlFile.close()

                  insertFrameAlias = "%s_insert" % fSpec.model.lower()

                  self.frames[insertFrameAlias] = FrameConfig(insertFrameAlias, insertFrameFileRef, fSpec.formClassName, "html")

                  for controllerAlias in self.controllers:
                      if self.controllers[controllerAlias].model == fSpec.model:                          
                          self.controllers[controllerAlias].addMethod(ControllerMethodConfig("insert", insertFrameAlias))
                           
                  # 
                  # update template: creates a form for modifying 
                  # a single object
                  
                  xslFilename = os.path.join("bootstrap", "update_template.xsl")
                  xslTree = etree.parse(xslFilename)
                  updateTemplateTransform = etree.XSLT(xslTree)
                  updateHTMLDoc = updateTemplateTransform(formSpecXML)

                  updateFilename = os.path.join("bootstrap", "%s_update.html" % fSpec.model.lower())
                  updateFrameFileRef =  "%s_update.html" % fSpec.model.lower()

                  htmlFile = open(updateFilename, "w")  
                  htmlFile.write(updateHTMLDoc.__str__())
                  htmlFile.close()

                  updateFrameAlias = "%s_update" % fSpec.model.lower()

                  self.frames[updateFrameAlias] = FrameConfig(updateFrameAlias, updateFrameFileRef, fSpec.formClassName, "html")

                  for controllerAlias in self.controllers:
                      if self.controllers[controllerAlias].model == fSpec.model:                                                    
                          self.controllers[controllerAlias].addMethod(ControllerMethodConfig("update", updateFrameAlias))

          finally:
              if xmlFile is not None:
                  xmlFile.close()
              if htmlFile is not None:
                  htmlFile.close()
              if xmlHandle is not None:
                  xmlHandle.close()
              if baseTemplateFile is not None:
                  baseTemplateFile.close()
                  
          
class DataSourceParameter:
    def __init__(self, name, value):
        self.name = name
        self.value = value


class DataSourceSpec:
    def __init__(self, type, parameterArray):
        self.type = type
        self.params = parameterArray

    
class FieldSpec:
    """A specification for a field in a WTForms form instance."""

    def __init__(self, name, label, type, required = False, hidden = False):
        self.name = name
        self.label = label
        self.type = type
        self.required = required
        self.hidden = hidden
        self.extraData = []

        if self.required:
            self.extraData.append("[validators.Required()]")

    def get_extraData(self):
        if len(self.extraData) == 0:
            return ""
        else:
            return ", " + ', '.join(self.extraDataFields)

    def __repr__(self):
        """The in-template representation of a FieldSpec."""

        if len(self.extraData) == 0:
            return "%s = %s(u'%s')" % (self.name, self.type.__name__, self.label)
        else:
            return "%s = %s(u'%s', %s)" % (self.name, self.type.__name__, self.label, ",".join(self.extraData))

class SelectFieldSpec(FieldSpec):

    def __init__(self, name, label, menuDict):
        FieldSpec.__init__(name, label, SelectField)
        
        menuChoices = []
        for key in menuDict:
            menuChoices.append("('%s', '%s')" % key, menuDict[key])

        self.extraData.append("choices = [%s]" % ",".join(menuChoices))

class FormSpec:
    """A specification for a WTForms form instance.

      A FormSpec instance, when serialized in XML format by SConfigurator.generateXMLFormSpecs(), 
      provides the basis for generating boilerplate code, templates, and Form instances 
      in Serpentine.
      """

    def __init__(self, model, urlBase):
        self.model = model
        self.urlBase = urlBase
        self.formClassName = "%sForm" % self.model
        self.fields = []

    def addField(self, fieldSpec):
        """Add the passed FieldSpec instance to this FormSpec."""

        self.fields.append(fieldSpec)

    def getField(self, name):
        """Retrieve a FieldSpec by name."""

        for field in self.fields:
            if field.name == name:
                return field

        raise NoSuchFieldSpecError(name)


class FieldSpecFactory:
    """Use Factory pattern to create a FieldSpec from reflected information about a database column."""

    def __init__(self):
        self.typeMap = { "BOOL": BooleanField, 
                         "INTEGER": IntegerField, 
                         "FLOAT": DecimalField, 
                         "DOUBLE": DecimalField, 
                         "DATE": DateField, 
                         "DATETIME": DateTimeField,
                         "INTEGER": IntegerField, 
                         "TINYINT": IntegerField, 
                         "VARCHAR": TextField }

        self.selectFields = {}
    
    def specifySelectField(self, name, dictionary):
        self.selectFields[name] = dictionary
        
    def create(self, tableColumn):
        """Create a field specification object based on the information in the column object.

        Arguments:
        --tableColumn: an SQLAlchemy reflected Column object 

        Returns:
        -- a valid FieldSpec instance
        """

        fieldName = tableColumn.name
        fieldLabel = self.convertColumnNameToLabel(tableColumn.name)

        if fieldName == "id":
            fieldType = HiddenField
            required = False
        elif fieldName in self.selectFields:
            return SelectFieldSpec(fieldName, fieldLabel, self.selectFields[fieldName])
        else:
            fieldType = self.determineFieldType(str(tableColumn.type))
            required = not tableColumn.nullable

        # TODO: Add some logic for finding out about hidden fields
        return FieldSpec(fieldName, fieldLabel, fieldType, required, False)
           

    def convertColumnNameToLabel(self, columnName):
        """Change a DB column name (all lowercase with an underscore separator)
           to capitalized names consisting of separate words in the case of a 
           compound name; i.e., 'street_address' becomes 'Street Address'. """

        result = []
        words = columnName.split("_")
        for word in words:
            result.append(word.capitalize())

        return ' '.join(result)
             
    def determineFieldType(self, fieldType):

        # first, strip out the parentheses; i.e. VARCHAR(20) should become VARCHAR

        openParenIndex = fieldType.find("(")
        closeParenIndex = fieldType.find(")")            
        rawName = fieldType[0 : openParenIndex]

        # futureproof: sometimes there is additional column type info, i.e., 'INTEGER(display_width=11)'
        extraData = fieldType[openParenIndex+1 : closeParenIndex]

        # try to look it up; if we don't know the type, default to text
        try:
            return self.typeMap[rawName]
        except KeyError:
            return TextField
           

class ControlSpec:
    """A specification for a Serpentine dynamic UI control.

    A ControlSpec is rendered directly into YAML by the SConfigurator.
    """

    def __init__(self, type, name, dataSourceAlias, templateID = None):
        self.type = type
        self.name = name
        self.datasource = dataSourceAlias
        self.template = templateID
        
        
def main():
        display = CursesDisplay(SConfigurator)
        display.open()
        
                                  
if __name__ == "__main__":
        main() 
    
    
    
            
            

      

