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


from sutility import *


ConfigMode = Enum(['CREATE', 'UPDATE'])
    

class ConfigurationPackage(object):
    def __init__(self, environment, **kwargs):
    
            #self.startup_db = None
            self.environment = environment
            self.frames = {}
            self.datasources = {}
            self.models = {}
          
            self.controls = {}
            self.frames = {}
            self.controllers = {}
            self.plugins = {}
            
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


    def clearModelConfigs(self):
        self.models.clear()


    def addControllerConfig(self, controllerConfig):
        self.controllers[controllerConfig.name] = controllerConfig


    def addPluginConfig(self, pluginConfig):
        self.plugins[pluginConfig.name] = pluginConfig


    def addFormConfig(self, formConfig):
        self.formConfigs.append(formConfig)
            

    def clearFormConfigs(self):
        del self.formConfigs[:]


    def getXMLFrames(self):
        return []
            

    def getStylesheet(self, assignedFrameAlias):
        pass
      

    #def getStylesheetPath(self):
    #raise Exception('accessing stylesheet_path value. Environment reads: %s' % self.environment.getStylesheetPath())


    app_name = property(lambda self: self.environment.getAppName())
    app_root = property(lambda self: self.environment.getAppRoot())
    app_version = property(lambda self: self.environment.getAppVersion())
    site_packages_directory = property(lambda self: self.environment.sitePackagesDirectory)
    
    web_app_name = property(lambda self: self.environment.getURLBase())
    hostname = property(lambda self: self.environment.hostname)
    port = property(lambda self: self.environment.port)
    startup_db = property(lambda self: self.environment.configurationDBAlias)
    xmlFrames = property(getXMLFrames)
    static_file_directory = property(lambda self: self.environment.getTemplateDirectory())
    template_directory = property(lambda self: self.environment.getTemplateDirectory())
    xsl_stylesheet_directory = property(lambda self: self.environment.getXSLStylesheetDirectory())
    url_base = property(lambda self: self.environment.getURLBase())
      
    default_form_package = property(lambda self: self.environment.config['global']['default_form_package'])
    default_model_package = property(lambda self: self.environment.config['global']['default_model_package'])
    default_controller_package = property(lambda self: self.environment.config['global']['default_controller_package'])
    default_helper_package = property(lambda self: self.environment.config['global']['default_helper_package'])
    default_reporting_package = property(lambda self: self.environment.config['global']['default_report_package'])
    
    default_responder_package = property(lambda self: self.environment.config['global']['default_responder_package'])
    default_datasource_package = property(lambda self: self.environment.config['global']['default_datasource_package'])
    
    #default_plugin_package = property(lambda self: self.environment.config['global']['default_plugin_package'])        
      


class SConfigurator(object):

    def __init__(self, **kwargs):
          self.config_filename = None
          self.environment = None
          self.mode = None


    def convertTableNameToModelName(self, tableName):
          """Convert an underscore-style db table name to a camel-cased class name."""

          # plural to singular
          tempName = tableName
          if tableName[-3:] == 'ies':
              tempName = tableName[0:-3] + 'y'
          elif tableName[-2:] == 'es':
              tempName = tableName[0:-2] 
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

    def getSiteDirLocation(self, screen, isUsingVirtualEnv, **kwargs):

        if not isUsingVirtualEnv:
            siteDirLocation = TextPrompt('Please enter the full path to your Python site directory.').show(screen)
        
        if isUsingVirtualEnv:
            virtualEnvHome = os.environ.get('WORKON_HOME')
            environments = []
            fileList = os.listdir(virtualEnvHome)
            for f in fileList:
                if os.path.isdir(os.path.join(virtualEnvHome, f)):
                    environments.append(f)

            envMenu = Menu(environments)

            while True:
                screen.clear()
                envPrompt = MenuPrompt(envMenu, 'Select the virtual environment this application will use.')
                selectedEnv = envPrompt.show(screen)

                if envPrompt.escaped:
                    Notice('You must select a virtual environment.' ).show(screen)
                    Notice('Hit any key to retry.').show(screen)
                    screen.getch()
                else:
                    pyVersions = os.listdir(os.path.sep.join([virtualEnvHome, selectedEnv, 'lib']))
                    versionMenu = Menu(pyVersions)
                    versionPrompt = MenuPrompt(versionMenu, 'Please select the python version you wish to use.')
                    pythonVersion = versionPrompt.show(screen)
                    if versionPrompt.escaped:
                        pythonVersion = 'python2.7' # default to 2.7
                    
                    siteDirLocation = os.path.sep.join([virtualEnvHome, selectedEnv, 'lib', pythonVersion, 'site-packages'])
                    break
                
        return siteDirLocation


    def run(self, screen, **kwargs):

          configFilename = kwargs.get('config_file', '')

          if configFilename:
              self.mode = ConfigMode.UPDATE              
              self.environment = Environment().bootstrap(configFilename)          
              globalSettings = self.setupGlobalData(screen, self.environment)              
          else:
              self.mode = ConfigMode.CREATE

              self.environment = Environment()
              prompt = TextPrompt('Are you using virtualenv and virtualenvwrapper to manage python dependencies (y/n)?', 'y')
              answer = prompt.show(screen)
              if answer == 'y':
                  siteDir = self.getSiteDirLocation(screen, True)
                  
              if answer == 'n':
                  Notice('We STRONGLY recommend that you install and configure virtualenv and virtualenvwrapper before using Serpentine.').show(screen)
                  if TextPrompt('Do you wish to exit and install these tools before proceeding (y/n)?', 'y').show(screen) == 'n':
                      siteDir = self.getSiteDirLocation(screen, False)
                  else:
                      return     # exit the program
                      
              self.environment.sitePackagesDirectory = siteDir

              Notice('Initializing Serpentine using Python site directory: %s' % siteDir).show(screen)
              Notice('Hit any key to continue.').show(screen)
              screen.getch()
              
              globalSettings = self.setupGlobalData(screen)
          
          # user's changes to settings override old values
          self.environment.importGlobalSettings(globalSettings)
          
          configPackage = ConfigurationPackage(self.environment)
          
          currentDir = os.getcwd()
          bootstrapDir = os.path.join(currentDir, "bootstrap")
          j2env = jinja2.Environment(loader = jinja2.FileSystemLoader(bootstrapDir))
          templateMgr = JinjaTemplateManager(j2env)


          self.mainSetup(configPackage, self.environment, templateMgr, screen)
          
          currentDir = os.getcwd()
          bootstrapDir = os.path.join(currentDir, "bootstrap")
          j2env = jinja2.Environment(loader = jinja2.FileSystemLoader(bootstrapDir))
          templateMgr = JinjaTemplateManager(j2env)
          
          screen.clear()
          Notice([' ', ':::[ Serpentine App Generator ]:::', ' ']).show(screen)   
         
          #--- Need to happen first?
          Notice('Generating application controller classes...').show(screen)
          self.generateControllerClasses(configPackage, templateMgr)   
          
          Notice('Generating HTML form classes...').show(screen)       
          self.generateFormClasses(configPackage, templateMgr)
          #---
         
          Notice('Generating application views...').show(screen)            
          contentFrames = self.generateApplicationTemplates(configPackage, templateMgr)

          for frame in contentFrames:
                configPackage.addFrameConfig(contentFrames[frame])
          
          Notice('Generating application model classes...').show(screen)
          self.generateModelClasses(configPackage)
          
          Notice('Generating configuration shell scripts...').show(screen)
          self.generateShellScripts(configPackage, templateMgr)
          
          # now generate the config file
          Notice('Generating Serpentine configuration file...').show(screen)
          self.generateConfigFile(configPackage, templateMgr)
        
          Notice('Done.').show(screen)
          Notice('Hit any key to exit.').show(screen)
          screen.getch()


    def mainSetup(self, configPackage, environment, templateManager, screen):
    
        mainMenu = Menu(['Global Settings', 
                         'Databases', 
                         'Models', 
                         'Views', 
                         'UI Controls',
                         'Plugins',
                         'Code Generator', 
                         'Web Config',
                         'Finish and Generate Files'])
        
        mainMenuPrompt = MenuPrompt(mainMenu, 'Please select a configuration activity.')
        
        databaseInstance = None
        wsgiConfig = None
        liveDB = False
        tableList = []
        uiControlConfigs = environment.exportUIControlConfigs()
        datasourceConfigs = environment.exportDataSourceConfigs()
        headerNotice = Notice([' ', ':::[ Serpentine Main Menu ]:::', ' '])
        
        while True:
            screen.clear()            
            headerNotice.show(screen)
            Notice(['web application: "%s" version %s' % (environment.getAppName(), environment.getAppVersion()), ' ']).show(screen)
            
            if databaseInstance:
                Notice(['connected to %s database "%s" on %s' %\
                (databaseInstance.dbType, databaseInstance.schema, databaseInstance.host), '']).show(screen)
            
            mainMenuPrompt.show(screen)
            
            if mainMenuPrompt.escaped:
                break
            
            if mainMenuPrompt.selectedIndex == 1: # Global Settings                  
                updatedSettings = self.setupGlobalData(screen, environment)
                environment.importGlobalSettings(updatedSettings)
                                
            if mainMenuPrompt.selectedIndex == 2: # Databases
                connected = not(databaseInstance is None)
                newDatabaseInstance = self.databaseSetup(configPackage, environment, screen, connected)
                if newDatabaseInstance:
                    databaseInstance = newDatabaseInstance
            
            if mainMenuPrompt.selectedIndex == 3:  # Models            
                if not databaseInstance:
                    Notice('Models: You must connect to a database in order to auto-generate model classes.').show(screen)
                    Notice('Select the "Databases" option and either set up a new DB or connect to an existing one.').show(screen)
                    Notice('Hit any key to continue.').show(screen)
                    screen.getch()
                    continue
            
                tableList = self.selectTables(databaseInstance, environment, screen)
          
                # TODO: Add parent-child mapping selection logic
                configPackage.clearModelConfigs()
                configPackage.clearFormConfigs()
                
                modelTableMap = self.createModelTableMap(tableList)
                
                for name in modelTableMap:
                    configPackage.addModelConfig(modelTableMap[name])

                formConfigArray = self.createFormConfigs(modelTableMap, environment)
                for fcfg in formConfigArray:
                    configPackage.addFormConfig(fcfg)

                # TODO: some frames will have helper functions
                #self.designateHelperFunctions(formConfigArray, screen)
    
                #datasourceConfigs = self.setupDatasources(environment, screen)
                #for name in datasourceConfigs:
                #      configPackage.addDatasourceConfig(datasourceConfigs[name], name)

                
            if mainMenuPrompt.selectedIndex == 4: # Views (Serpentine Frames) 
                Notice('Views: This section is not yet functional.').show(screen)
                Notice('Hit any key to continue.').show(screen)
                screen.getch()
                continue
                
            if mainMenuPrompt.selectedIndex == 5:  # UIControls
                if not databaseInstance:
                    Notice('UI Controls: You must connect to a database in order to manage data-driven UI controls.').show(screen)
                    Notice('Select the "Databases" option and either set up a new DB or connect to an existing one.').show(screen)
                    Notice('Hit any key to continue.').show(screen)
                    screen.getch()
                else:                                        
                    self.setupUIControls(uiControlConfigs, datasourceConfigs, databaseInstance, environment, screen)
                    configPackage.controls.update(uiControlConfigs)
                    configPackage.datasources.update(datasourceConfigs)


            if mainMenuPrompt.selectedIndex == 6: # Plugins
                pluginConfigs = self.setupPlugins(environment, screen)
                configPackage.plugins.update(pluginConfigs)
                
 
            if mainMenuPrompt.selectedIndex == 7: # Code Generator
                self.generateCodeSegments(configPackage, uiControlConfigs, environment, templateManager, screen)

                
            if mainMenuPrompt.selectedIndex == 8: # WSGI Settings
                 wsgiConfig = self.setupWSGI(screen, wsgiConfig)          
                 environment.importWSGIConfig(wsgiConfig)

            if mainMenuPrompt.selectedIndex == 9: # Finish and generate files                
                break
        
    
    def databaseSetup(self, configPackage, environment, screen, connected=False):
    
        dbSetupMenu = Menu(['Create new database configuration', 'Browse/edit databases', 'Connect to database'])
        dbSetupMenuPrompt = MenuPrompt(dbSetupMenu, 'Please select a database activity.')
        databaseInstance = None
        headerNotice = Notice([' ', ':::[ Serpentine Database Configuration Section ]:::', ' '])
        
        while True:
            screen.clear()
            headerNotice.show(screen)
            
            if databaseInstance:
                Notice(['connected to %s database "%s" on %s' %\
                (databaseInstance.dbType, databaseInstance.schema, databaseInstance.host), '']).show(screen)
            elif connected:
                activeConfig = configPackage.databases[environment.configDBAlias]
                Notice(['connected to %s database %s on host %s' %\
                (activeConfig.dbType, activeConfig.schema, activeConfig.host), '']).show(screen)
                
            
            selection = dbSetupMenuPrompt.show(screen)
            
            if dbSetupMenuPrompt.escaped:
                if not databaseInstance and not connected:                        
                    Notice('You have not connected to a live database instance.').show(screen)
                    Notice('You will not be able to auto-generate Model classes or create data-driven UI controls.').show(screen)
                    exit = TextPrompt('Really exit to main menu (y/n)?', 'n').show(screen)
                    if exit == 'y':
                        break                    
                    else: 
                        dbSetupMenuPrompt.reset()
                        continue                
                elif not databaseInstance and connected:
                    Notice('You have not created a new database connection.').show(scren)
                    Notice('Your existing connection will be used to generate Model classes and create data-driven controls.').show(screen)
                    exit = TextPrompt('Really exit to main menu (y/n)?', 'y').show(screen)
                    if exit == 'y':
                        break                    
                    else: 
                        continue
                else:
                    break
            
            if dbSetupMenuPrompt.selectedIndex == 1:  # New DB config
                hostname = TextPrompt("Host where database resides", "localhost").show(screen)
                schema = TextPrompt("Enter database schema", environment.getURLBase()).show(screen)
                username = TextPrompt("Enter database username", None).show(screen)
                password = TextPrompt("Enter database password", None).show(screen)
                dbConfigName = TextPrompt("Enter a name for this database instance", "localhost.%s" % schema).show(screen)
                  
                newConfig = DatabaseConfig(hostname, schema, username, password)
                environment.importDatabaseSettings({dbConfigName: newConfig})
                configPackage.addDatabaseConfig(newConfig, dbConfigName)
                
                screen.addstr("\n New database created. Hit any key to continue.")
                screen.getch()
                    
            if dbSetupMenuPrompt.selectedIndex == 2: # Browse/Edit                            
                if not configPackage.databases:                  
                    Notice(["You haven't created any database configurations.", "Hit any key to continue."]).show(screen)
                    screen.getch()
                else:
                    dbConfigMenu = Menu(configPackage.databases.keys())
                    dbConfigPrompt = MenuPrompt(dbConfigMenu, 'Select a database configuration to edit')
                    dbConfigName = dbConfigPrompt.show(screen)
                    
                    if not dbConfigPrompt.escaped:
                        dbConfig = configPackage.databases[dbConfigName]
    
                        hostname = TextPrompt('Enter updated database host', dbConfig.host).show(screen)
                        schema = TextPrompt('Enter updated database schema', dbConfig.schema).show(screen)
                        username = TextPrompt('Enter updated database username', dbConfig.username).show(screen)
                        password = TextPrompt('Enter updated database password', dbConfig.password).show(screen)
                          
                        updatedDBConfig = DatabaseConfig(hostname, schema, username, password)
                        #configPackage.databases.pop(dbName)
                        environment.importDatabaseSettings({dbConfigName: updatedDBConfig})
                        configPackage.addDatabaseConfig(updatedDBConfig, dbConfigName)
                            
                        Notice('Database configuration updated. Hit any key to continue.').show(screen)
                        screen.getch()
             
            if dbSetupMenuPrompt.selectedIndex == 3:    # Connect to database
                                  
                 if not configPackage.databases:
                     Notice('You have not configured any databases.').show(screen)
                     Notice('Hit any key to continue.').show(screen)
                     screen.getch()
                 else:
                     screen.clear()
                     headerNotice.show(screen)
                     dbConnectMenu = Menu(configPackage.databases.keys())
                     dbConnectMenuPrompt = MenuPrompt(dbConnectMenu, 'Select a target database to connect to')
                     targetDBAlias = dbConnectMenuPrompt.show(screen)
                     
                     if not dbConnectMenuPrompt.escaped:
                         targetDBConfig = configPackage.databases[targetDBAlias]
                                                  
                         while True:
                            try:
                                databaseInstance = self.connectToDatabase(targetDBConfig)
                                Notice('Connected to database %s on host %s as user %s. Hit any key to continue.' % \
                                (targetDBConfig.schema, targetDBConfig.host, targetDBConfig.username)).show(screen)
                                environment.configurationDBAlias = targetDBAlias
                                
                                screen.getch()
                                break
                            except Exception, err:
                                
                                Notice(['Error logging into database %s on host %s:' % \
                                (targetDBConfig.schema, targetDBConfig.host), err.message]).show(screen)
                                
                                Notice([' ', 'Please check your hostname, schema, username, and password.']).show(screen)
                                retryPrompt = TextPrompt('Retry (y/n)?', 'y').show(screen)
                    
                                if retryPrompt == 'n':                                        
                                    break
                                else:
                                    targetDBConfig.host = TextPrompt('hostname', targetDBConfig.host).show(screen)
                                    targetDBConfig.schema = TextPrompt('schema', targetDBConfig.schema).show(screen)
                                    targetDBConfig.username = TextPrompt('username', targetDBConfig.username).show(screen)
                                    targetDBConfig.password = TextPrompt('password', targetDBConfig.password).show(screen)
                                    
        return databaseInstance      
                       
                         
                         
                         
    def connectToDatabase(self, dbConfig):        
            dbInstance = db.MySQLDatabase(dbConfig.host, dbConfig.schema)
            dbInstance.login(dbConfig.username, dbConfig.password)
            return dbInstance                        

        

    def setupPlugins(self, environment, screen):
        pluginSetupMenu = Menu(['Create new plugin', 'Browse/edit existing plugin configs', 'Set user plugin module'])
        prompt = MenuPrompt(pluginSetupMenu, 'Please select a plugin activity.')
        headerNotice = Notice([' ', ':::[ Serpentine Plugin Configuration Section ]:::', ' '])

        # TODO: initialize with existing configs on subsequent calls
        plugins = {}
        
        while not prompt.escaped:
              screen.clear()              
              headerNotice.show(screen)
              Notice('Register one or more plugins to handle specialized tasks.').show(screen)
              selection = prompt.show(screen)
              if prompt.escaped:
                  break
              if prompt.selectedIndex == 1: # new plugin
                  pluginClassname = TextPrompt("Enter plugin class name", None).show(screen)
                  pluginAlias = TextPrompt("Enter an alias for this plugin", None).show(screen)
                  pluginModule = TextPrompt('Enter the Python module name for this plugin [user_plugins]', None)
                  pluginConfig = PluginConfig(pluginClassname, pluginAlias, pluginModule)
                  
                                                      
                  while True:                      
                      slotPrompt = TextPrompt('Create new slot for plugin "%s" (%d existing slots) y/n?' \
                                          % (pluginConfig.alias, len(pluginConfig.slots)), 'y')
                      choice = slotPrompt.show(screen)
                      if choice == 'n':
                          break
                      else:
                          routeNotice = \
                          Notice(["Enter a URL route: one or more strings separated by forward slashes.",
                                  "(Strings representing variables must have leading colons.)",
                                  "The URL route directs an inbound HTTP request to the specified method for this slot;",
                                  "for example, search/:widget_id might be the route for a plugin function that searches for a user-supplied id.", "\n"])
                          routeNotice.show(screen)
                                                    
                          route = TextPrompt('Enter a URL route for this plugin slot: ').show(screen)

                          methodNotice = Notice(["\n", "Next enter a method name.",
                                                 "The plugin method name you specify will be invoked by Serpentine",
                                                 "when it receives a URL on the specified route.", "\n"])
                          methodNotice.show(screen) 
                          
                          methodName = TextPrompt('Enter a plugin method name for this slot: ').show(screen)
                          
                          requestTypes = {'get': 'GET', 'post': 'POST' }
                          requestType = TextSelectPrompt('Select the HTTP request type for this plugin slot: ', requestTypes).show(screen)
                          
                          pluginConfig.addSlot(PluginSlotConfig(methodName, route, requestType))

                          Notice(['\n', 'Slot created: URL route %s will invoke method "%s" on plugin class %s for HTTP %s requests.' \
                                  % (route, methodName, pluginClassname, requestType)]).show(screen)
                          

                                  #Notice('Done.').show(screen)                          
                          Notice('Hit any key to continue.').show(screen)
                          screen.getch()
                          screen.clear()
                          headerNotice.show(screen)

                  plugins[pluginConfig.alias] = pluginConfig
                  screen.addstr("\n New plugin created and registered. Hit any key to continue.")
                  screen.getch()
                  screen.clear()
                          
              if prompt.selectedIndex == 2:     # edit a plugin configuration
                  screen.clear()
                  headerNotice.show(screen)
                  if not len(plugins.keys()):                  
                      Notice(["You haven't configured any plugins.", "Hit any key to continue."]).show(screen)
                      screen.getch()
                  else:
                      pluginMenu = Menu(plugins.keys())
                      pluginPrompt = MenuPrompt(pluginMenu, 'Select a plugin configuration to edit')
                      Notice('').show(screen)
                      pluginAlias = pluginPrompt.show(screen)
                      pluginConfig = plugins[pluginAlias]
                      
                      #alias = TextPrompt('Enter updated plugin alias', pluginConfig.alias).show(screen)

                      slotConfigSectionHeader = Notice('Plugin "%s" has the following slots configured: ')
                      slotMenu = Menu(pluginConfig.listSlots())
                      slotPrompt = MenuPrompt(slotMenu, 'Select a plugin slot to update')
                      
                      while not slotPrompt.escaped:
                          slotConfigSectionHeader.show(screen)
                          slotName = slotPrompt.show(screen)
                          if slotPrompt.escaped:
                              break
                          
                          pluginSlot = pluginConfig.getSlot(slotName)
                          updatedRoute = TextPrompt('URL route for this plugin slot: ', pluginSlot.route_extension).show(screen)
                          updatedMethod = TextPrompt("Target method for this slot's URL route: ", pluginSlot.method).show(screen)
                          updatedRequestType = TextPrompt('HTTP request type for this slot: ', pluginSlot.request_type).show(screen)
                          
                          pluginSlot.route_extension = updatedRoute
                          pluginSlot.method = updatedMethod
                          pluginSlot.request_type = updatedRequestType
                          
                          Notice('Plugin slot updated. Hit any key to continue.').show(screen)
                          screen.getch()
                          screen.clear()
                          headerNotice.show(screen)
                  screen.clear()
              if prompt.selectedIndex == 3: # Designate the python module which will hold user plugins
                  pass
                  """
                  screen.clear()
                  headerNotice.show(screen)

                  Notice('')
                  p = TextPrompt('Load existing python module')
                  
                  pluginFileListing = self.getCandidatePluginModules()
                  moduleNameMenu = Menu(pluginFileListing)
                  moduleNamePrompt
                  """
                
        return plugins

    
    def generateCodeSegments(self, configPackage, uiConfigs, environment, templateManager, screen):
    
        codeGenMenu = Menu(['Generate Serpentine URLs', 'Generate Javascript segments'])
        cgMenuPrompt = MenuPrompt(codeGenMenu, 'Select the type of code you wish to generate:')
        
        
        jsSegmentToTemplateMap = {'UI Control': 'js_uicontrol_segment.tpl'}
        urlTypeToTupleMap = { 'Frame': ('url_frame_request.tpl', self.setupFrameRequestURLPackage), 
                            'Controller': ('url_controller_call.tpl', self.setupControllerURLPackage), 
                            'Responder': ('url_responder_call.tpl', self.setupResponderURLPackage), 
                            'UI Control': ('url_uicontrol.tpl', self.setupUIControlURLPackage) }
                            
        urlTypeMenu = Menu(urlTypeToTupleMap.keys())
        jsSegmentTypeMenu = Menu(jsSegmentToTemplateMap.keys())
        headerNotice = Notice([' ', ':::[ Serpentine Code Segment Generator ]:::', ' '])
        
        while(True):            
            screen.clear()
            headerNotice.show(screen)
            selection = cgMenuPrompt.show(screen)
            
            if cgMenuPrompt.escaped:
                break
                
            if cgMenuPrompt.selectedIndex == 1: # Generate URLs  
                screen.clear()
                headerNotice.show(screen)                                          
                segmentMenuPrompt = MenuPrompt(urlTypeMenu, 'Generate a URL for which object type?')
                segmentType = segmentMenuPrompt.show(screen)                
                
                if segmentMenuPrompt.escaped:
                    continue
                
                urlTemplateFilename = urlTypeToTupleMap[segmentType][0] # indexes into a tuple
                setupFunction = urlTypeToTupleMap[segmentType][1]
                
                segmentPackage = setupFunction(configPackage, screen)
                if not segmentPackage:
                    return
                
                renderCodeSegment(urlTemplateFilename, 
                                  segmentPackage, 
                                  configPackage, 
                                  environment, 
                                  templateManager, 
                                  screen)
                                  
            
            if cgMenuPrompt.selectedIndex == 2: # Generate Javascript segments
                screen.clear()
                headerNotice.show(screen)
                segmentMenuPrompt = MenuPrompt(jsSegmentTypeMenu, 'Generate Javascript for which object type?')                
                segmentType = segmentMenuPrompt.show(screen)      
                
                if segmentMenuPrompt.escaped:
                    continue
                          
                javascriptTemplateFilename = jsSegmentToTemplateMap[segmentType]
                
                if segmentType == 'UI Control':
                    controlPackage = self.setupUIControlURLPackage(configPackage, screen)
                    if not controlPackage:
                        break
                    self.renderCodeSegment(javascriptTemplateFilename, 
                                        controlPackage, 
                                        configPackage, 
                                        environment, 
                                        templateManager, 
                                        screen)
                    
    
    def setupFrameRequestURLPackage(self, configPackage, screen):
    
        if not configPackage.frames:
            Notice(['You have not created any content frames.', '', 
                    'Hit any key to continue.']).show(screen)
            screen.getch()
            return None
    
        frameMenu = Menu(configPackage.frames)
        frameID = MenuPrompt(frameMenu, 'Select the Serpentine Frame you want to request').show(screen)
        return FrameRequestURLPackage('frame', frameID)
        
                    
    def setupControllerURLPackage(self, configPackage, screen):    
        controllerMenu = Menu(configPackage.controllers)
        controllerID = MenuPrompt(controllerMenu, 'Select the controller you want to call').show(screen)
        methodName = TextPrompt('Type the name of the controller method you wish to invoke').show(screen)        
        return ControllerURLPackage('controller', controllerID)
        
    
    def setupResponderURLPackage(self, configPackage, screen):
        responderMenu = Menu(configPackage.responders)
        responderID = MenuPrompt(responderMenu, 'Select the responder you want to call').show(screen)    
        return ResponderURLPackage('responder', responderID)
    
    
    def setupUIControlURLPackage(self, configPackage, screen):
    
        if not configPackage.controls:
            Notice(['You have not created any UI controls.', 
                    'Please select UI Controls from the main menu to create a UI control.', '', 
                    'Hit any key to continue.']).show(screen)
            screen.getch()
            return None
        
        uiControlMenu = Menu(configPackage.controls.keys())
        controlID = MenuPrompt(uiControlMenu, 'Select the Serpentine UI Control you want to render').show(screen)        
        targetDiv = TextPrompt('Target <div> id in the target HTML page', 'div_id').show(screen)
        callbackName = TextPrompt('Javascript callback function to be called post-render', 'null').show(screen)
        htmlName = TextPrompt('HTML name for this control', 'anonymous').show(screen)
        
        controlParams = []
        controlParams.append(ObjectParameter('name', htmlName))
        
        while True:
            addParameter = TextPrompt('Add another name/value parameter to the control (y/n)?', 'n').show(screen)
            if addParameter == 'y':
                paramName = TextPrompt('Control parameter name').show(screen)
                paramValue = TextPrompt('Control parameter value').show(screen)
                controlParams.append(ObjectParameter(paramName, paramValue))
            else:
                break
        
        return ControlPackage(controlID, targetDiv, controlParams, callbackName)
         
        
        
                
    
    def renderCodeSegment(self, templateName, dataPackage, configPackage, environment, templateManager, screen):
    
        screen.clear()
        Notice([' ', ':::[ Serpentine Code Segment Generator ]:::', ' ']).show(screen)
        segmentTemplate = templateManager.getTemplate(templateName)
        segment = segmentTemplate.render(config = configPackage, control = dataPackage)
        Notice(segment).show(screen)
        Notice([' ', 'Hit any key to continue.']).show(screen)
        screen.getch()
    
                 



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


    def _addLookupTable(self, lookupTableArray, databaseInstance, environment, screen):
          screen.clear()
          tablesToAdd = self.selectTables(databaseInstance, environment, screen)
          tableNames = [table.name for table in tablesToAdd]
          result = lookupTableArray
          result.extend(tableNames)
          return result


    def _removeLookupTable(self, lookupTableArray, screen):
          
          result = lookupTableArray
          prompt = MultipleChoiceMenuPrompt(Menu(result), 'Select one or more tables to remove from the list.')
          while not prompt.escaped:
              screen.clear()
              tablesToRemove = prompt.show(screen)
              if not prompt.escaped:
                  Notice('Removing tables %s from lookups.' % tablesToRemove).show()
                  result = [item for item in lookupTableArray if item not in tablesToRemove]
          return result


    def setupUIControls(self, uiControls, datasourceConfigs, databaseInstance, environment, screen):
          """Set up zero or more UI controls, to be rendered via templates and supplied with data
          via datasources
          """

          menu = Menu(['Create a custom data-bound HTML control', 'Browse existing HTML controls'])
          #if self.mode == ConfigMode.CREATE:
          menu.addItem('Auto-create HTML select controls from lookup tables')
            
          prompt = MenuPrompt(menu, 'Select an option from the menu to manage HTML controls.')

                   
          while not prompt.escaped:
            screen.clear()
            Notice([' ', ':::[ Serpentine UI Control Configuration Menu ]:::', ' ']).show(screen)
            prompt.show(screen)
            
            if prompt.escaped:
                break

            
            if prompt.selectedIndex == 1: # create new control
                  newControlConfig = self.createUIControl(uiControls, datasourceConfigs, databaseInstance, environment, screen)
                  uiControls[newControlConfig.name] = newControlConfig                  
               
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
                self._autoGenerateControls(uiControls, datasourceConfigs, databaseInstance, environment, screen)

          return 



    def createUIControl(self, uiControlMap, datasourceConfigMap, databaseInstance, environment, screen):
        controlNameOK = False
        controlName = None
        headerNotice = Notice([':::[ Serpentine UI Control Configuration Section ]:::', ''])
                  
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
        # specify control type, datasource, and template

        screen.clear()
        headerNotice.show(screen)
        
        controlTypeMenu = Menu(['select', 'radiogroup', 'table'])
        controlTypePrompt = MenuPrompt(controlTypeMenu, 'Select an HTML control type.')
        controlType = controlTypePrompt.show(screen)

        # control types are select, table, radiogroup
        # valid datasource types are "menu" and "table"

        datasources = None
        
        controlNotice = Notice('Setting up %s-type UIControl "%s"' % (controlType, controlName))
        
        while True:
            screen.clear()
            headerNotice.show(screen)
            controlNotice.show(screen)
            if controlType == 'select':
                datasources = self._getDatasourceAliasesForControlType('menu', datasourceConfigMap)
            if controlType == 'radiogroup':
                datasources = self._getDatasourceAliasesForControlType('menu', datasourceConfigMap)
            if controlType == 'table':
                datasources = self._getDatasourceAliasesForControlType('table', datasourceConfigMap)

            if not datasources:
                Notice('No compatible datasources have been created for a %s-type control.' % controlType).show(screen)
                shouldCreateSources =TextPrompt('Create one or more new datasources (y/n)?', 'y').show(screen)
                if shouldCreateSources == 'y':
                    newDatasourceConfigs = self.setupDataSources(databaseInstance, environment, screen)
                    datasourceConfigMap.update(newDatasourceConfigs)
                else:
                    Notice('Cannot create a live UIControl without a datasource. Hit any key to exit to the main menu.').show(screen)
                    screen.getch()
                    return None
            else:
                break

        screen.clear()
        headerNotice.show(screen)
        controlNotice.show(screen)
        datasourceMenu = Menu(datasources)        
        datasourcePrompt = MenuPrompt(datasourceMenu, 'Select the datasource that will populate the control.')
        datasourceName = datasourcePrompt.show(screen)

        newControl = ControlConfig(controlType, controlName, datasourceName)

        Notice('Created new %s-type HTML control "%s" linked to datasource "%s".' % (controlType, controlName, datasourceName)).show(screen)
        Notice('Hit any key to continue.').show(screen)
        screen.getch()
        return newControl


    def _getDatasourceAliasesForControlType(self, controlTypeName, datasourceConfigs):

        result = []
        for key in datasourceConfigs:
            dsConfig = datasourceConfigs[key]
            if dsConfig.type == controlTypeName:
                result.append(key)

        return result
            

    
    def _autoGenerateControls(self, uiControls, datasourceConfigs, databaseInstance, environment, screen):
    
        actionMenu = Menu(['Generate Controls', 'Add Lookup Table', 'Show Lookup Tables', 'Remove Lookup Table', 'Clear Lookup Tables'])
        actionPrompt = MenuPrompt(actionMenu, 'Select an action to manage lookup tables.')
        
        
        targetDBConfig = environment.databases[environment.configurationDBAlias]
        dbInstance = db.MySQLDatabase(targetDBConfig.host, targetDBConfig.schema)
        dbInstance.login(targetDBConfig.username, targetDBConfig.password)
        
        tableList = dbInstance.listTables()          
        lookupTables = [table for table in tableList if table[0:7] == 'lookup_']
        
        
        while not actionPrompt.escaped:
            screen.clear()
            Notice([' ', ':::[ Serpentine UIControl Generator ]:::', ' ']).show(screen)
            Notice('Serpentine will autogenerate HTML select controls from lookup tables in the database.').show(screen)
            Notice(['(Tables already bound to controls will be marked with an arrow.)', '']).show(screen)
            
            
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
                lookupTables = self._addLookupTable(lookupTables, databaseInstance, environment, screen)
      
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


    def setupDataSources(self, database, environment, screen):
          """Specify zero or more data 'adapters' to populate UI controls & other data-driven types"""

          sourceConfigs = environment.exportDataSourceConfigs()

          options = ['Create new data source', 'Browse/Edit data sources']
          
          
          prompt = MenuPrompt(Menu(options), 'Select an option from the menu.')
          

          
          while not prompt.escaped:
              screen.clear()
              Notice([' ', ':::[ Serpentine Datasource Configuration Page ]:::', ' ']).show(screen)
              Notice('Create one or more datasources to populate UI controls.').show(screen)
              selection = prompt.show(screen)
              if prompt.escaped:
                  break
              if prompt.selectedIndex == 1: # create datasource
                  sourceNamePrompt = TextPrompt('Enter a name for the datasource')
                  sourceName = sourceNamePrompt.show(screen)
                  
                  sourceTypeOptions = ['menu', 'table']
                  sourceTypePrompt = MenuPrompt(Menu(sourceTypeOptions), 'Select a datasource type.')
                  sourceType = sourceTypePrompt.show(screen)
                  
                  sourceParams = []
                  
                  table = self.selectSingleTable(screen, database, environment, 'Select the target table for the datasource.')
                  screen.clear()
                  sourceParams.append(DataSourceParameter('table', table.name))
                  
                  if sourceType == 'menu':
                      # prompt for the name and value fields (usually the 'name' and 'id' columns)
                      Notice('Table "%s" selected. Select source fields next.' % table.name)
                      columnNames = [column.name for column in table.columns]                      
                      columnMenu = Menu(columnNames)
                      valueFieldPrompt = MenuPrompt(columnMenu, 'Select the value field (usually the primary key field).')
                      valueField = valueFieldPrompt.show(screen)
                      nameFieldPrompt = MenuPrompt(columnMenu, 'Select the name field (usually the value displayed in menus or other controls).')
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


    def _createGlobalSettings(self, screen):
            screen.clear()
            settings = {}
            
            Notice([' ', ':::[ Serpentine Global Configuration Screen ]:::', ' ']).show(screen)
            #Notice('Welcome to SConfigurator, the Serpentine auto-config utility.').show(screen)
            

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
          
          Notice([' ', ':::[ Serpentine Global Configuration Screen ]:::', ' ']).show(screen)
          #Notice('Welcome to SConfigurator, the Serpentine auto-config utility.').show(screen)
          Notice('Update project information for the Serpentine web app "%s"' % settings['app_name']).show(screen)

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

            # these are local to their respective sections in the config, so they are relative paths
            globalSettings['static_file_directory'] =  "templates"
            globalSettings['template_directory'] = "templates"
            globalSettings['xsl_stylesheet_directory'] = "stylesheets"
                       
            globalSettings['default_form_package'] = '%s_forms' % globalSettings['web_app_name'].lower()
            globalSettings['default_model_package'] = '%s_models' % globalSettings['web_app_name'].lower()
            globalSettings['default_controller_package'] = '%s_controllers' % globalSettings['web_app_name'].lower()
            globalSettings['default_helper_package'] = '%s_helpers' % globalSettings['web_app_name'].lower()
            globalSettings['default_responder_package'] = '%s_responders' % globalSettings['web_app_name'].lower()
            # globalSettings['default_plugin_package'] = 'user_plugins' 
            globalSettings['default_report_package'] = '%s_reports' % globalSettings['web_app_name'].lower()
            globalSettings['default_datasource_package'] = '%s_datasources' % globalSettings['web_app_name'].lower()
            
            staticFilePath = os.path.join(globalSettings['app_root'], globalSettings['static_file_directory'])
            scriptPath = os.path.join(globalSettings['app_root'], globalSettings['static_file_directory'], 'scripts')
            stylesPath = os.path.join(globalSettings['app_root'], globalSettings['static_file_directory'], 'styles')
            xmlPath = os.path.join(globalSettings['app_root'], globalSettings['static_file_directory'], 'xml')
            xslStylesheetPath = os.path.join(globalSettings['app_root'], globalSettings['xsl_stylesheet_directory'])
            
            try:
                if not os.path.exists(staticFilePath):
                    os.system('mkdir %s' % staticFilePath) 

                if not os.path.exists(scriptPath):
                    os.system('mkdir %s' % scriptPath)

                if not os.path.exists(stylesPath):
                    os.system('mkdir %s' % stylesPath)

                if not os.path.exists(xmlPath):
                    os.system('mkdir %s' % xmlPath)
                    
                if not os.path.exists(xslStylesheetPath):
                    os.system('mkdir %s' % xslStylesheetPath)

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



    def selectTables(self, dbInstance, environment, screen):
            screen.clear()
            # get a listing of all tables and present in menu form
            
            header = Notice(['', ':::[ Serpentine Model Generator ]:::', '',
             'Selected tables will be used to autogenerate Serpentine model classes.', ''])
            
            m = Menu(dbInstance.listTables())
            
            prompt = MultipleChoiceMenuPrompt(m, 'Select one or more database tables', environment.tables, header)
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
      
          
    def setupWSGI(self, screen, existingWSGIConfig = None):
          """Get the settings for the app's interface with Apache

          Arguments:
          screen -- display target for menus and prompts
          """
          

          screen.clear()
                    
          if not existingWSGIConfig:
              defaultHostname = 'localhost'
              defaultPort = 80
          else:
              defaultHostname = existingWSGIConfig.host
              defaultPort = existingWSGIConfig.port
          
          Notice([' ', ':::[ Serpentine WSGI Configuration Screen ]:::', ' ']).show(screen)
          Notice('Enter WSGI config information.').show(screen)
          hostPrompt = TextPrompt('Enter the hostname for this app: ', defaultHostname)
          hostname = hostPrompt.show(screen)

          portPrompt = TextPrompt('Enter HTTP port for this app: ', defaultPort)
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


    def generateSingleTemplate(self, sourceTemplateFilename, outputTemplateFilename, configPackage, templateManager):
        
        templateObject = templateManager.getTemplate(sourceTemplateFilename)
        templateData = templateObject.render(config = configPackage)
        outputTemplateFullPath = os.path.join('bootstrap', outputTemplateFilename)
        templateFile = open(outputTemplateFullPath, 'w')
        templateFile.write(templateData)
        templateFile.close()


    def generatePluginCode(self, pluginConfig):
        pass
        

    def generateApplicationTemplates(self, configPackage, templateManager):
        """Create the master template files for the application under construction"""

        #xmlHandle = None

        htmlFile = None
        baseTemplateFile = None

        generatedFiles = {}
        frames = {}
        try:
            # TODO: Factor these sections down into a series of function calls
            #
            # The file that connects user-defined routes with plugin methods
            #
            if len(configPackage.plugins.keys()):
                slots = []
                modules = []
                for p in configPackage.plugins:
                    slots.extend(configPackage.plugins[p].slots)
                    moduleName = configPackage.plugins[p].modulename
                    if moduleName not in modules:
                        modules.append(moduleName)

                Notice(['Generating plugin %s into the Python module %s.py in the <app_root>/plugins directory...' \
                                  % (p.modulename)]).show(screen)
                self.generatePluginCode(p)
                
                
                pluginRoutingTemplate = templateManager.getTemplate('plugin_routing_template.tpl')
                pluginRoutingFilename = os.path.join('bootstrap', 'plugin_routes.py')
                pluginRoutingFile = open(pluginRoutingFilename, 'w')
                try:
                    routingBlock = pluginRoutingTemplate.render(plugin_modules = modules, plugin_slots = slots)
                    pluginRoutingFile.write('%s\n' % routingBlock)                    
                except Exception, err:
                    raise err
                finally:
                    if pluginRoutingFile:
                        pluginRoutingFile.close()

                
                

            
            # The base HTML template from which our other templates will inherit
            #
            # self.generateSingleTemplate('base_html_template.tpl', 'base_template.html', configPackage, templateManager)
            
            baseTemplate = templateManager.getTemplate('base_html_template.tpl')
            baseTemplateData = baseTemplate.render(config = configPackage)
            baseTemplateFilename = os.path.join('bootstrap', 'base_template.html')
            baseTemplateFile = open(baseTemplateFilename, 'w')
            baseTemplateFile.write(baseTemplateData)
            baseTemplateFile.close()

            # Render the default error page which will show when a system-level exception is thrown
            #
            errorTemplate = templateManager.getTemplate('error_html_template.tpl')
            errorTemplateData = errorTemplate.render(config = configPackage)
            errorTemplateFilename = os.path.join('bootstrap', 'error.html')
            errorTemplateFile = open(errorTemplateFilename, 'w')
            errorTemplateFile.write(errorTemplateData)
            errorTemplateFile.close()

            # The default login page
            loginTemplate = templateManager.getTemplate('login_html_template.tpl')
            loginTemplateData = loginTemplate.render(config = configPackage)
            loginTemplateFilename = os.path.join('bootstrap', 'login.html')
            loginTemplateFile = open(loginTemplateFilename, 'w')
            loginTemplateFile.write(loginTemplateData)
            loginTemplateFile.close()
            
            
            # The default access-denied page which will show if a user lacks the privileges
            # to access a secured object
            deniedTemplate = templateManager.getTemplate('denied_html_template.tpl')
            deniedTemplateData = deniedTemplate.render(config=configPackage)
            deniedTemplateFilename = os.path.join('bootstrap', 'denied.html')
            deniedTemplateFile = open(deniedTemplateFilename, 'w')
            deniedTemplateFile.write(deniedTemplateData)
            deniedTemplateFile.close()
                    
            # The index template, for viewing all objects of a given type
            indexSeedTemplate = templateManager.getTemplate('index_template_seed.tpl')
            for fConfig in configPackage.formConfigs:
                    #
                    # Use each FormConfig object in our list to populate the seed template
                    # 
                    
                                      
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
                          controllerConfig = configPackage.controllers[controllerAlias]
                          if controllerConfig.model == fConfig.model:
                                controllerConfig.addMethod(ControllerMethodConfig('index', indexFrameAlias))

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
                          if configPackage.controllers[controllerAlias].model == fConfig.model:                          
                                configPackage.controllers[controllerAlias].addMethod(ControllerMethodConfig("insert", insertFrameAlias))
                           
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
                                
                    #
                    # delete template: creates a form (really a confirmation page) for deleting an object
                    #
                    
                    deleteSeedTemplate = templateManager.getTemplate('delete_template_seed.tpl')
                    deleteSeedTemplateData = deleteSeedTemplate.render(formspec = fConfig, config = configPackage)
                    
                    deleteFilename = os.path.join('bootstrap', '%s_delete.html' % fConfig.model.lower())
                    
                    htmlFile = open(deleteFilename, 'w')
                    htmlFile.write(deleteSeedTemplateData)
                    htmlFile.close()
                    
                    deleteFrameFileRef = '%s_delete.html' % fConfig.model.lower()
                    deleteFrameAlias = '%s_delete' % fConfig.model.lower()
                    
                    frames[deleteFrameAlias] = FrameConfig(deleteFrameAlias, deleteFrameFileRef, fConfig.formClassName, 'html')
                    
                    for controllerAlias in configPackage.controllers:
                        if configPackage.controllers[controllerAlias].model == fConfig.model:
                            configPackage.controllers[controllerAlias].addMethod(ControllerMethodConfig('delete', deleteFrameAlias))
                            
                    
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
    
    
    
            
            

      

