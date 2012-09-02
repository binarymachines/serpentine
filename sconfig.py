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
from metaobjects import *
import argparse


class Enum(set):
    def __getattr__(self, name):
        if name in self:
            return name
        raise AttributeError


ConfigMode = Enum(['CREATE', 'UPDATE'])
    

class ConfigurationPackage(object):
    def __init__(self, environment, **kwargs):
            self.environment = environment
            self.frames = {}
            self.datasources = {}
            self.models = {}
          
            self.controls = {}
            self.frames = {}
            self.controllers = {}
            
            self.views = {}
            self.databases = {}
            self.responders = {}
            self.helpers = {}

            self.formConfigs = []


    def addDatabaseConfig(self, dbConfig, name):
        self.databases[name] = dbConfig
      

    def addFrameConfig(self, fConfig):
        self.frames[fConfig.name] = fConfig


    def addDatasourceConfig(self, dConfig, name):
        self.datasources[name] = dConfig


    def addUIControlConfig(self, controlConfig, name):
        self.controls[name] = controlConfig


    def addModelConfig(self, modelConfig):
        self.models[modelConfig.name] = modelConfig


    def addControllerConfig(self, controllerConfig):
        self.controllers[controllerConfig.name] = controllerConfig


    def addFormConfig(self, formConfig):
        self.formConfigs.append(formConfig)
            

    def getXMLFrames(self):
        return []
            

    def getStylesheet(self, assignedFrameAlias):
        pass
      


    app_name = property(lambda self: self.environment.getAppName())
    app_root = property(lambda self: self.environment.getAppRoot())
    app_version = property(lambda self: self.environment.getAppVersion())
    web_app_name = property(lambda self: self.environment.getURLBase())
    hostname = property(lambda self: self.environment.hostname)
    port = property(lambda self: self.environment.port)
    xmlFrames = property(getXMLFrames)
    static_file_path = property(lambda self: self.environment.getTemplatePath())
    template_path = property(lambda self: self.environment.getTemplatePath())
    stylesheet_path = property(lambda self: self.environment.getStylesheetPath())
    url_base = property(lambda self: self.environment.getURLBase())
      
    default_form_package = property(lambda self: self.environment.config['global']['default_form_package'])
    default_model_package = property(lambda self: self.environment.config['global']['default_model_package'])
    default_controller_package = property(lambda self: self.environment.config['global']['default_controller_package'])
    default_helper_package = property(lambda self: self.environment.config['global']['default_helper_package'])
    default_reporting_package = property(lambda self: self.environment.config['global']['default_report_package'])
    default_responder_package = property(lambda self: self.environment.config['global']['default_responder_package'])
            
      


class SConfigurator(object):

    def __init__(self, **kwargs):

          self.startup_db = None
          self.config_filename = None
          self.environment = None
          self.mode = None


    def convertTableNameToModelName(self, tableName):
          """Convert an underscore-style db table name to a camel-cased class name."""

          # plural to singular
          tempName = tableName
          if tableName[-3:] == 'ies':
              tempName = tableName[0:-3] + 'y'
          elif tableName[-1:] == 's':
              tempName = tableName[0:-1]

          # remove the underscore separator and camel-case any compound names
          underscoreIndex = tempName.find('_')
          if underscoreIndex != -1:
              pieces = [tempName[0: underscoreIndex].capitalize(), tempName[underscoreIndex+1:].capitalize()]
              className = ''.join(pieces)
          else:       
              className = tempName.capitalize()

          return className


    def run(self, screen, **kwargs):

          configFilename = kwargs.get('config_file', '')
          
          if configFilename:
              self.mode = ConfigMode.UPDATE              
              self.environment = Environment().bootstrap(configFilename)          
              globalSettings = self.setupGlobalData(screen, self.environment)              
          else:
              self.mode = ConfigMode.CREATE              
              globalSettings = self.setupGlobalData(screen)
              self.environment = Environment()
          
          
          
          # user's changes to settings override old values
          self.environment.importGlobalSettings(globalSettings)

          databases = self.setupDatabases(screen, self.environment) 
          self.environment.importDatabaseSettings(databases)

          configPackage = ConfigurationPackage(self.environment)

          for dbName in databases:
              configPackage.addDatabaseConfig(databases[dbName], dbName)

          # we need the database connection to be live
          #self.environment.initializeDataStore()
          databaseInstance = self.connectToDatabase(screen, self.environment)

          if databaseInstance:
              tableList = self.selectTables(screen, databaseInstance, self.environment)
          
              # TODO: Add parent-child mapping selection logic
              modelTableMap = self.createModelTableMap(tableList)

              for name in modelTableMap:
                    configPackage.addModelConfig(modelTableMap[name])

              formConfigArray = self.createFormConfigs(modelTableMap, self.environment)
              for fcfg in formConfigArray:
                  configPackage.addFormConfig(fcfg)

              # TODO: some frames will have helper functions
              #self.designateHelperFunctions(formConfigArray, screen)
    
              #datasourceConfigs = self.setupDatasources(screen, self.environment)
              #for name in datasourceConfigs:
              #      configPackage.addDatasourceConfig(datasourceConfigs[name], name)
    
              
              if len(tableList):
                  uiControlConfigs = self.environment.exportUIControlConfigs()
                  datasourceConfigs = self.environment.exportDataSourceConfigs()
                  self.setupUIControls(screen, uiControlConfigs, datasourceConfigs, self.environment)
                  
                  for name in uiControlConfigs:                
                        configPackage.addUIControlConfig(uiControlConfigs[name], name)
          
          
          wsgiConfig = self.setupWSGI(screen)
          
          self.environment.importWSGIConfig(wsgiConfig)
          
          currentDir = os.getcwd()
          bootstrapDir = os.path.join(currentDir, "bootstrap")
          j2env = jinja2.Environment(loader = jinja2.FileSystemLoader(bootstrapDir))
          templateMgr = JinjaTemplateManager(j2env)
                    
          

          contentFrames = self.generateApplicationTemplates(configPackage, templateMgr)

          for frame in contentFrames:
                configPackage.addFrameConfig(contentFrames[frame])
          
          
          self.generateModelClasses(configPackage)
          self.generateControllerClasses(configPackage, templateMgr)          
          self.generateFormClasses(configPackage, templateMgr)
          self.generateShellScripts(configPackage, templateMgr)
          
          # now generate the config file
          self.generateConfigFile(configPackage, templateMgr)
          


    def generateConfigFile(self, configPackage, templateMgr):
            configFile = None
            wsgiFile = None
            wsgiVHostEntryFile = None
            
            try:
                  configFileTemplate = templateMgr.getTemplate('config_template.tpl')
                  configFilename = '%s.conf' % configPackage.web_app_name
                  configFile = open(os.path.join('bootstrap', configFilename), 'w')
                  configFile.write(configFileTemplate.render(config = configPackage))
                  #configFile.close()
              
                  wsgiFile = open(os.path.join('bootstrap', '%s.wsgi' % configPackage.web_app_name), 'w')
                  wsgiFileTemplate = templateMgr.getTemplate("wsgi_file.tpl")
                  wsgiData = wsgiFileTemplate.render(config = configPackage)
                  wsgiFile.write(wsgiData)
                  #wsgiFile.close()

                  wsgiVHostEntryFile = open(os.path.join('bootstrap', '%s_vhost_entry.xml' % configPackage.web_app_name), 'w')
                  wsgiVHostTemplate = templateMgr.getTemplate('wsgi_vhost_entry.tpl')
                  wsgiVHostData = wsgiVHostTemplate.render(config = configPackage)
                  wsgiVHostEntryFile.write(wsgiVHostData)

                  self.config_filename = configFilename
            finally:
                  if configFile:
                        configFile.close()

                  if wsgiFile:
                        wsgiFile.close()

                  if wsgiVHostEntryFile:
                        wsgiVHostEntryFile.close()

            
      
    def designateHelperFunctions(self, formConfigs, screen):
          """Allow the user to specify a helper function for one or more frames"""

          pass


    def _addLookupTable(self, lookupTableArray, screen, environment):
          screen.clear()
          tablesToAdd = self.selectTables(screen, environment)
          tableNames = [table.name for table in tablesToAdd]
          result = lookupTableArray
          result.extend(tableNames)
          return result


    def _removeLookupTable(self, lookupTableArray, screen):
          
          result = lookupTableArray
          prompt = MultipleChoiceMenuPrompt(result, 'Select one or more tables to remove from the list.')
          while not prompt.escaped:
              screen.clear()
              tablesToRemove = prompt.show(screen)
              if not prompt.escaped:
                  Notice('Removing tables %s from lookups.' % tablesToRemove).show()
                  result = [item for item in lookupTableArray if item not in tablesToRemove]
          return result




    def setupUIControls(self, screen, uiControls, datasourceConfigs, environment):
          """Set up zero or more UI controls, to be rendered via templates and supplied with data
          via datasources
          """

          menu = Menu(['Create a custom data-bound HTML control', 'Browse existing HTML controls'])
          #if self.mode == ConfigMode.CREATE:
          menu.addItem('Auto-create HTML select controls from lookup tables')
            
          prompt = MenuPrompt(menu, 'Select an option from the menu to manage HTML controls.')

                   
          while not prompt.escaped:
            screen.clear()
            prompt.show(screen)
            
            if prompt.escaped:
                break

            
            if prompt.selectedIndex == 1: # create new control
                  newControlMap = self.createUIControl(screen, uiControls, datasourceConfigs, environment)
                  controlMap.update(newControlMap)

               
            if prompt.selectedIndex == 2:   # browse existing controls
                if not len(uiControls.keys()):
                    Notice('You have not created any UI controls yet.').show(screen)
                    Notice('Hit any key to continue.').show(screen)
                    screen.getch()
                else:
                    controlMenu = Menu(uiControls.keys())
                    controlSelectPrompt = MenuPrompt(controlMenu, 'Select a UIControl to inspect.')
                    
                    while not controlSelectPrompt.escaped:
                        screen.clear()
                        Notice('UI controls in the %s Serpentine app:' % environment.getAppName()).show(screen)
                        controlName = controlSelectPrompt.show(screen)
                        
                        if controlSelectPrompt.escaped:
                            break
                            
                        if controlName in uiControls:
                            screen.clear()
                            controlConfig = uiControls[controlName]
                            Notice('[ UIControl: %s ] type: %s, datasource: %s' \
                            % (controlName, controlConfig.type, controlConfig.datasource)).show(screen)
                            shouldInspect = TextPrompt("Inspect control's Datasource (y/n)?", 'n').show(screen)
                            if shouldInspect == 'y':
                                dsConfig = datasourceConfigs[controlConfig.datasource]
                                Notice('[ DataSource: %s ] %s' % (controlConfig.datasource, dsConfig)).show(screen)
                            
                            Notice('hit any key to continue').show(screen)
                            screen.getch()
                  
            if prompt.selectedIndex == 3: #  Auto-generate from lookup tables
                self._autoGenerateControls(screen, uiControls, datasourceConfigs, environment)

          return 



    def createUIControl(self, screen, uiControlMap, datasourceConfigMap, environment):
        controlNameOK = False
        controlName = None
                  
        while not controlNameOK:
            controlName = TextPrompt('Name for the new UI control (alphanumeric chars only, no spaces):').show(screen)
            
            # TODO: check for bad chars
            rx = re.compile('[^a-zA-Z0-9_]')
            if rx.search(controlName):
                Notice('Valid control names must contain letters, numbers, and underscores only.').show(screen)
                Notice('Hit any key to continue.').show(screen)
                screen.getch()
            else:
                controlNameOK = True
                          
                if controlName in uiControlMap:
                    overwrite = TextPrompt('That name is already in use. Overwrite existing control y/n?', 'n').show(screen)
                    if overwrite == 'n':
                        controlNameOK = False
                        
        # Now generate the control
        
        return {}


    
    def _autoGenerateControls(self, screen, uiControls, datasourceConfigs, environment):
    
        actionMenu = Menu(['Generate Controls', 'Add Lookup Table', 'Show Lookup Tables', 'Remove Lookup Table', 'Clear Lookup Tables'])
        actionPrompt = MenuPrompt(actionMenu, 'Select an action to manage lookup tables.')
        
        
        targetDBConfig = environment.databases[self.startup_db]
        dbInstance = db.MySQLDatabase(targetDBConfig.host, targetDBConfig.schema)
        dbInstance.login(targetDBConfig.username, targetDBConfig.password)
        
        tableList = dbInstance.listTables()          
        lookupTables = [table for table in tableList if table[0:7] == 'lookup_']
        
        
        while not actionPrompt.escaped:
            screen.clear()
            Notice('Serpentine will autogenerate HTML select controls from lookup tables in the database.').show(screen)
            Notice('(Tables already bound to controls will be marked with an arrow.)').show(screen)
            Notice('Compiling list...').show(screen)
            
            # find out all the tables that have already been bound to controls
            boundTables = []                
            for cfg in datasourceConfigs.values():
              boundTables.extend([p.value for p in cfg.params if p.name == 'table'])
                    
            # Mark the bound tables in the display list 
            lookupTableDisplayList = []
            for t in lookupTables:
                if t in boundTables:
                    lookupTableDisplayList.append(t + ' <=\n')
                else:
                    lookupTableDisplayList.append(t + '\n')
                    
            selection = actionPrompt.show(screen)
            index = actionPrompt.selectedIndex
            
            if actionPrompt.escaped:
                break

            if index == 1:  # generate
                Notice('Generating HTML select controls for selected lookup tables.').show(screen)
                ignoreExisting = TextPrompt('Ignore tables already bound to controls y/n?', 'y').show(screen)
                
                if ignoreExisting == 'y':            
                    targetList = []
                    targetList = [t for t in lookupTables if not t in boundTables]
                else:
                    targetList = lookupTables
                
                Notice('OK. Generating controls for the following tables: \n%s ' % '\n'.join(targetList)).show(screen)
                
                for tableName in targetList:
                    parameterSet = []
                    parameterSet.append(DataSourceParameter('table', tableName))
                    parameterSet.append(DataSourceParameter('name_field', 'name'))
                    parameterSet.append(DataSourceParameter('value_field', 'id'))
                    sourceName = '%s_src' % tableName
                    datasourceConfigs[sourceName] = DataSourceConfig('menu', parameterSet)
              
                    controlName = '%s_select' % tableName
                    uiControls[controlName] = ControlConfig('select', controlName, sourceName)
                
                Notice('hit any key to continue.').show(screen)
                screen.getch()
                    
            if index == 2: # add 
                lookupTables = self._addLookupTable(lookupTables, screen, environment)
      
            if index == 3: # show
                Notice(lookupTableDisplayList).show(screen)
                Notice('Hit any key to continue.').show(screen)
                screen.getch()

            if index == 4:  # remove
                lookupTables = self._removeLookupTable(lookupTables, screen)
              
            if index == 5: # clear the list
                lookupTables = []
      
            #screen.clear()
        return 
    
    
    def _addSelectControl(self, screen):
          pass


    def _addRadioControl(self, screen):
          pass


    def _addTableControl(self, screen):
          pass


    def setupDatasources(self, screen, environment):
          """Specify zero or more data 'adapters' to populate UI controls & other data-driven types"""

          sourceConfigs = environment.exportDatasourceConfigs()

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
                  
                  sourceTypeOptions = ['menu', 'table']
                  sourceTypePrompt = MenuPrompt(Menu(sourceTypeOptions), 'Select a datasource type.')
                  sourceType = sourceTypePrompt.show(screen)
                  
                  sourceParams = []

                  table = self.selectSingleTable(screen, environment, 'Select the target table for the datasource.')
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

                  if sourceType == 'table':
                      fieldListPrompt = MultipleChoiceMenuPrompt(columnNames, 'Select one or more columns from the source table.')
                      selectedFields = fieldListPrompt.show(screen)
                      sourceParams.append(DataSourceParameter('fields', ','.join(selectedFields)))
                      

                  newConfig = DataSourceConfig(sourceType, sourceParams)
                  sourceConfigs[sourceName] = newConfig

              if prompt.selectedIndex == 2:     # list existing sources
                  screen.addstr("\nDatasources: " + ", ".join(sourceConfigs.keys()) + "\nHit any key to continue.")
                  screen.getch()

              screen.clear()
              return sourceConfigs



    def setupDatabases(self, screen, environment):
          """Allow the user to specify one or more named database instances from which to select later"""

          options = ["Create new database configuration", "List databases", "Edit database settings"]
          databases = environment.exportDatabaseSettings() 

          prompt = MenuPrompt(Menu(options), "Select an option from the menu.")
          screen.clear()
          Notice('Set up one or more database instances to connect to from the web application.').show(screen)
          while not prompt.escaped:
              selection = prompt.show(screen)
              if prompt.escaped:
                  break
              if prompt.selectedIndex == 1:
                  schema = TextPrompt("Enter database schema", environment.getURLBase()).show(screen)
                  username = TextPrompt("Enter database username", None).show(screen)
                  password = TextPrompt("Enter database password", None).show(screen)
                  dbName = TextPrompt("Enter a name for this database instance", "localhost.%s" % schema).show(screen)
                  
                  databases[dbName] = DatabaseConfig("localhost", schema, username, password)
                  screen.addstr("\n New database created. Hit any key to continue.")
                  screen.getch()
                  screen.clear()
              if prompt.selectedIndex == 2:     # list existing databases
                  screen.addstr("\nDatabases: " + ", ".join(databases.keys()) + "\nHit any key to continue.")
                  screen.getch()
                  screen.clear()

              if prompt.selectedIndex == 3:
                  screen.clear()
                  dbMenu = Menu(databases.keys())
                  dbPrompt = MenuPrompt(dbMenu, 'Select a database configuration to edit')
                  dbName = dbPrompt.show(screen)
                  dbConfig = databases[dbName]
                  
                  schema = TextPrompt('Enter updated database schema', dbConfig.schema).show(screen)
                  username = TextPrompt('Enter updated database username', dbConfig.username).show(screen)
                  password = TextPrompt('Enter updated database password', dbConfig.password).show(screen)
                  newDBName = TextPrompt('Enter an updated name for this database instance', dbName).show(screen)
                  
                  updatedDBConfig = DatabaseConfig('localhost', schema, username, password)

                  if newDBName == dbName:
                      databases[newDBName] = updatedDBConfig
                  else:
                      databases.pop(dbName)
                      databases[newDBName] = updatedDBConfig
                  
                  Notice('Database configuration updated. Hit any key to continue.').show(screen)
                  screen.getch()
                  screen.clear()
                  
          return databases


    def _createGlobalSettings(self, screen):
            screen.clear()
            settings = {}
            
            Notice('Welcome to SConfigurator, the Serpentine auto-config utility.').show(screen)
            Notice('Set basic project information for the web app.').show(screen)

            projectNamePrompt = TextPrompt("Enter project name", None)
            settings['app_name'] = projectNamePrompt.show(screen)            
            settings['web_app_name'] = settings['app_name'].lower()
            settings['url_base'] = settings['app_name'].lower()

            currentDir = os.getcwd()
            settings['app_root'] = currentDir
            
            projectVersionPrompt = TextPrompt('Enter application version number', '1.0')
            settings['app_version'] = projectVersionPrompt.show(screen)
            
            return settings
            


    def _updateGlobalSettings(self, screen, legacySettings):
          screen.clear()
          settings = legacySettings
          
          Notice('Welcome to SConfigurator, the Serpentine auto-config utility.').show(screen)
          Notice('Update project information for existing Serpentine app: %s' % settings['app_name']).show(screen)

          projectNamePrompt = TextPrompt('Project name', settings['app_name'])
          settings['app_name'] = projectNamePrompt.show(screen)
          settings['web_app_name'] = settings['app_name'].lower()
          settings['url_base'] = settings['app_name'].lower()
          
          projectVersionPrompt = TextPrompt('Enter application version number', settings['app_version'])
          settings['app_version'] = projectVersionPrompt.show(screen)

          
          return settings
          
          

    def setupGlobalData(self, screen, environment = None):
            """Set project values which will be used by various sections of the configuration.

            Here is where we set the project name, basic path information, and packages names for generated MVC classes.

            Arguments:
            screen -- curses display context
            """

            if not environment:
                globalSettings =  self._createGlobalSettings(screen)
            else:
                globalSettings =  self._updateGlobalSettings(screen, environment.exportGlobalSettings())


            
          

            # this is a standalone global in the config, so it must be an absolute path
            globalSettings['static_file_path'] = os.path.join(globalSettings['app_root'], "templates") 

            # these are local to their respective sections in the config, so they are relative paths
            globalSettings['template_path'] = "templates"
            globalSettings['stylesheet_path'] = "stylesheets"
                       
            globalSettings['default_form_package'] = '%s_forms' % globalSettings['web_app_name'].lower()
            globalSettings['default_model_package'] = '%s_models' % globalSettings['web_app_name'].lower()
            globalSettings['default_controller_package'] = '%s_controllers' % globalSettings['web_app_name'].lower()
            globalSettings['default_helper_package'] = '%s_helpers' % globalSettings['web_app_name'].lower()
            globalSettings['default_responder_package'] = '%s_responders' % globalSettings['web_app_name'].lower()
            globalSettings['default_report_package'] = '%s_reports' % globalSettings['web_app_name'].lower()
            globalSettings['default_datasource_package'] = '%s_datasources' % globalSettings['web_app_name'].lower()
            

            scriptPath = [globalSettings['static_file_path'], 'scripts']
            stylesPath = [globalSettings['static_file_path'], 'styles']
            xmlPath = [globalSettings['static_file_path'], 'xml']
            
            try:
                if not os.path.exists(globalSettings['static_file_path']):
                    os.system('mkdir %s' % globalSettings['static_file_path']) 
                
                if not os.path.exists(globalSettings['stylesheet_path']):
                    os.system('mkdir %s' % globalSettings['stylesheet_path'])

                if not os.path.exists(os.path.join(scriptPath[0], scriptPath[1])):
                    os.system('mkdir %s' % os.path.join(scriptPath[0], scriptPath[1]))

                if not os.path.exists(os.path.join(stylesPath[0], stylesPath[1])):
                    os.system('mkdir %s' % os.path.join(stylesPath[0], stylesPath[1]))

                if not os.path.exists( os.path.join(xmlPath[0], xmlPath[1])):
                    os.system('mkdir %s' % os.path.join(xmlPath[0], xmlPath[1]))

                return globalSettings
            except IOError, err:
                raise err


            
            

    def selectSingleTable(self, screen, dbInstance, environment, screenMsg = None):          
          screen.clear()
          if screenMsg:
              Notice(screenMsg).show(screen)
              
          selectedTable = None

          try:
              # get a listing of all tables and present in menu form
              m = Menu(dbInstance.listTables())
              prompt = MenuPrompt(m, 'Select a database table.')
              tableName = prompt.show(screen)                                                   
              selectedTable = dbInstance.getTable(tableName)          
              return selectedTable
          finally:
              pass


    def connectToDatabase(self, screen, environment):
        screen.clear()
        dbPrompt = MenuPrompt(Menu(environment.databases.keys()), "Select a DB instance to connect to.")
            
        dbName = None
        while not dbName:
            dbName = dbPrompt.show(screen)                    
            if not dbName:
                Notice('You cannot autogenerate models or forms or create data-bound controls without connecting to a database.').show(screen)            
                skipDBConnect = TextPrompt('Are you sure you want to skip this step (y/n)?', 'n').show(screen)
                
                if skipDBConnect == 'y':
                    break
                    
        if not dbName:
            return None
        else:
            dbConfig = environment.databases[dbName]
            self.startup_db = dbName

            dbInstance = None
            while True:
                try:
                    # first connect to the DB                
                    dbInstance = db.MySQLDatabase(dbConfig.host, dbConfig.schema)
                    dbInstance.login(dbConfig.username, dbConfig.password)
                    Notice('Connected to database %s on host %s as user %s. Hit any key to continue.' % \
                    (dbConfig.schema, dbConfig.host, dbConfig.username)).show(screen)
                    screen.getch()
                    break
                except Exception, err:
                    Notice(['Error logging into database %s on host %s:' % (dbConfig.schema, dbConfig.host), err.message]).show(screen)
                    Notice([' ', 'Please check your username and password.']).show(screen)
                    retryPrompt = TextPrompt('Retry (y/n?', 'y').show(screen)
                    
                    if retryPrompt == 'n':
                        Notice('Returning to previous screen. Live-data configuration features will be unavailable.').show(screen)
                        Notice('Hit any key to continue.').show(screen)
                        dbInstance = None
                        screen.getch()
                        break
                    else:
                        dbConfig.username = TextPrompt('username').show(screen)
                        dbConfig.password = TextPrompt('password').show(screen)
                        continue
            return dbInstance



    def selectTables(self, screen, dbInstance, environment):
            screen.clear()
            # get a listing of all tables and present in menu form
            m = Menu(dbInstance.listTables())
            prompt = MultipleChoiceMenuPrompt(m, 'Select one or more database tables to add.', environment.tables)
            selectedTableNames = prompt.show(screen)

            selectedTables = []
            for name in selectedTableNames:                                        
                selectedTables.append(dbInstance.getTable(name))
        
            return selectedTables
           


    def createModelTableMap(self, selectedTables):
          """ use the names of the selected tables to generate camel-cased class names.

          Arguments:
          selectedTables -- an array of SQLAlchemy Table objects reflected from the current DB schema
          screen -- the curses graphical context object
          """

          modelTableMap = {}
          for table in selectedTables:
              modelName = self.convertTableNameToModelName(table.name)
              modelTableMap[modelName] = ModelConfig(modelName, table, None)

          # for now, accept all generated model names. TODO: eventually allow changes.
         
          return modelTableMap
         

    def generateModelClasses(self, configPackage):
          """Generate all boilerplate Model classes, in a single module

          Arguments: 
          modelNames -- an array of model names
          """     
          modelPkg = os.path.join("bootstrap", "%s.py" % configPackage.default_model_package) 
          f = open(modelPkg, "a")
          #f.write("#!/usr/bin/python\n\n")
          for modelName in configPackage.models:
              f.write("\nclass %s(object): pass" % modelName)
              f.write("\n\n")
          f.close()


    def createFormConfigs(self, modelTableMap, environment):
          """For each model name in the dictionary, generate form specification (FormConfig) object.

          Arguments:
          modelTableMap -- a dictionary of table objects in our schema, indexed by model classnames. 
                           The expression modelTableMap['Widget'] would yield the SQLAlchemy Table object 
                           corresponding to "widgets" in the database.
          
          Returns:
          an array of FormConfig instances
          """

          formConfigs = []

          try:        
              factory = FieldConfigFactory()
              for modelName in modelTableMap:                  
                  # formspecs need the URL base to properly generate action URLs in the HTML templates
                  newFormConfig = FormConfig(modelName, environment.getURLBase()) 
                  modelConfig = modelTableMap[modelName]

                  table = modelConfig.table
                  
                  for column in table.columns:
                      newFormConfig.addField(factory.create(column))

                  formConfigs.append(newFormConfig)
                  
              return formConfigs
          finally:
              pass
      
          
    def setupWSGI(self, screen):
          """Get the settings for the app's interface with Apache

          Arguments:
          screen -- display target for menus and prompts
          """
          

          screen.clear()
          wsgiSetup = {}
          Notice('Enter WSGI config information.').show(screen)
          hostPrompt = TextPrompt('Enter the hostname for this app: ', 'localhost')
          hostname = hostPrompt.show(screen)

          portPrompt = TextPrompt('Enter HTTP port for this app: ', '80')
          port = portPrompt.show(screen)

          return WSGIConfig(hostname, port)
          
          
    def generateShellScripts(self, configPackage, templateManager):
          """Generate the shell scripts to be used for post-config setup
          
          templateManager -- repository holding refs to all our file templates
          """

          scriptFile = None

          try:
              scriptTemplate = templateManager.getTemplate('setup_content_refs.tpl')
              scriptData = scriptTemplate.render(config = configPackage)
              scriptFilename = os.path.join('bootstrap', 'setup_content_refs.sh')
              scriptFile = open(scriptFilename, 'w')
              scriptFile.write(scriptData)
              result = subprocess.call(['chmod', 'u+x', scriptFilename])
          finally:
              if scriptFile:
                  scriptFile.close()
          
          

    def generateFormClasses(self, configPackage, templateManager):
          """Create the WTForms Form instances for the application under construction

          Arguments:
          configPackage -- a bundle of application data 
          templateManager -- repository holding refs to all our file templates
          """

          formPkgTemplate = templateManager.getTemplate("forms_package.tpl")
          formPkgString = formPkgTemplate.render(formspecs = configPackage.formConfigs)
          
          # write the package string out to a file
          formPkgName = os.path.join("bootstrap", "%s_forms.py" % configPackage.web_app_name)
          formPkgFile = open(formPkgName, "w")
          formPkgFile.write(formPkgString)
          formPkgFile.close()


    def generateControllerClasses(self, configPackage, templateManager):        
        """Generate Python package specifying the app's controller classes"""

        controllerPkgFile = None

        try:
            for fConfig in configPackage.formConfigs:
                controllerClassName = "%sController" % fConfig.model
                controllerAlias = fConfig.model
                modelClassName = fConfig.model
                configPackage.controllers[controllerAlias] = ControllerConfig(controllerClassName, controllerAlias, modelClassName)

            controllerPkgTemplate = templateManager.getTemplate("controllers_package.tpl")
            controllerPkgString = controllerPkgTemplate.render(config = configPackage)

            controllerPkgName = os.path.join("bootstrap", "%s_controllers.py" % configPackage.web_app_name)

            controllerPkgFile = open(controllerPkgName, "w")
            controllerPkgFile.write(controllerPkgString)
            controllerPkgFile.close()
        finally:
            if controllerPkgFile:
                controllerPkgFile.close()


    def generateApplicationTemplates(self, configPackage, templateManager):
        """Create the master template files for the application under construction"""

        #xmlHandle = None

        htmlFile = None
        baseTemplateFile = None

        generatedFiles = {}
        frames = {}
        try:
            # First render the base HTML template from which our other templates will inherit
            #
            baseTemplate = templateManager.getTemplate('base_html_template.tpl')
            baseTemplateData = baseTemplate.render(config = configPackage)
            baseTemplateFilename = os.path.join('bootstrap', 'base_template.html')
            baseTemplateFile = open(baseTemplateFilename, 'w')
            baseTemplateFile.write(baseTemplateData)
            baseTemplateFile.close()

              
            for fConfig in configPackage.formConfigs:
                    #
                    # Use each FormConfig object in our list to populate the seed template
                    # 

                    # The index template, for viewing all objects of a given type
                  
                    indexSeedTemplate = templateManager.getTemplate('index_template_seed.tpl')
                    indexSeedTemplateData = indexSeedTemplate.render(formspec = fConfig, config = configPackage)

                    # Now write the actual HTML model index file 

                    indexFilename = os.path.join("bootstrap", "%s_index.html" % fConfig.model.lower())
                  
                    htmlFile = open(indexFilename, "w")   
                    htmlFile.write(indexSeedTemplateData)
                    htmlFile.close()
                  
                    indexFrameFileRef = "%s_index.html" % fConfig.model.lower()
                    indexFrameAlias = "%s_index" % fConfig.model.lower()
                    frames[indexFrameAlias] = FrameConfig(indexFrameAlias, indexFrameFileRef, fConfig.formClassName, "html")
                  
                    for controllerAlias in configPackage.controllers:
                          if configPackage.controllers[controllerAlias].model == fConfig.model:
                                configPackage.controllers[controllerAlias].addMethod(ControllerMethodConfig('index', indexFrameAlias))

                    # 
                    # The insert template: creates a form for adding a single object
                    #
                  
                    insertSeedTemplate = templateManager.getTemplate('insert_template_seed.tpl')
                    insertSeedTemplateData = insertSeedTemplate.render(formspec = fConfig, config = configPackage)

                    # now write the actual HTML model insert file

                    insertFilename = os.path.join("bootstrap", "%s_insert.html" % fConfig.model.lower())
                  
                    htmlFile = open(insertFilename, "w")  
                    htmlFile.write(insertSeedTemplateData)
                    htmlFile.close()

                    insertFrameFileRef = "%s_insert.html" % fConfig.model.lower()
                    insertFrameAlias = "%s_insert" % fConfig.model.lower()

                    frames[insertFrameAlias] = FrameConfig(insertFrameAlias, insertFrameFileRef, fConfig.formClassName, "html")

                    for controllerAlias in configPackage.controllers:
                          if self.controllers[controllerAlias].model == fConfig.model:                          
                                self.controllers[controllerAlias].addMethod(ControllerMethodConfig("insert", insertFrameAlias))
                           
                    # 
                    # update template: creates a form for modifying 
                    # a single object
                  
                    updateSeedTemplate = templateManager.getTemplate('update_template_seed.tpl')
                    updateSeedTemplateData = updateSeedTemplate.render(formspec = fConfig, config = configPackage)

                    # now write the file

                    updateFilename = os.path.join("bootstrap", "%s_update.html" % fConfig.model.lower())

                    htmlFile = open(updateFilename, "w")  
                    htmlFile.write(updateSeedTemplateData)
                    htmlFile.close()
                  
                    updateFrameFileRef =  "%s_update.html" % fConfig.model.lower()
                    updateFrameAlias = "%s_update" % fConfig.model.lower()

                    frames[updateFrameAlias] = FrameConfig(updateFrameAlias, updateFrameFileRef, fConfig.formClassName, "html")

                    for controllerAlias in configPackage.controllers:
                          if configPackage.controllers[controllerAlias].model == fConfig.model:                                                    
                                configPackage.controllers[controllerAlias].addMethod(ControllerMethodConfig('update', updateFrameAlias))
            return frames                 
        finally:
              if htmlFile:
                  htmlFile.close()
              if baseTemplateFile:
                  baseTemplateFile.close()
              


def main():
        parser = argparse.ArgumentParser(description = \
        'Serpentine auto-configuration script.\n\noptional arguments: filename: the name of an existing config file')
        
        parser.add_argument('strings', metavar='filename', nargs='?',
                            help='an existing Serpentine config file')

        args = parser.parse_args()
        
                
        if not args.strings:        # User invoked sconfig with no arguments; new configuration
            display = CursesDisplay(SConfigurator)
            display.open()
        else:                       # User invoked sconfig with existing config file; edit configuration
            configFilename = None
            try:
                currentDir = os.getcwd()
                configFilename = os.path.join(currentDir, args.strings)
                print 'Configuration file: %s' % configFilename
                display = CursesDisplay(SConfigurator)
                display.open(config_file = configFilename)
                
            except IOError, err:
                sys.exit('Serpentine config file %s not found.' % configFilename)
            
         
   
        
                                  
if __name__ == "__main__":
        main() 
    
    
    
            
            

      

