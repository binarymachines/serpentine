#!/usr/bin/python


import npyscreen as ns
import curses
import os


import db
import content
import metaobjects as meta
import environment as env
import sconfig



UICONTROL_MENU_OPTIONS = ['Create a custom data-bound HTML control', 'Browse existing HTML controls', 'Auto-create HTML select controls']
UICONTROL_TYPE_OPTIONS = ['select', 'radiogroup', 'table']
DATASOURCE_TYPE_OPTIONS = ['menu', 'table']


class NoSuchDataSourceException(Exception):
    def __init__(self, dataSourceAlias):
        Exception.__init__('No DataSource has been registered under the alias %s.' % dataSourceAlias)

        
class NoSuchControlConfigException(Exception):
    def __init__(self, configAlias):
        Exception.__init__('No UIControl configuration has been registered under the alias %s.' % configAlias)


class GlobalSettingsForm(ns.ActionForm):
    def create(self):
        self.value = None
        self.projectName  = self.add(ns.TitleText, name = "Project name:")
        self.versionNumber = self.add(ns.TitleText, name = "Version number:")
        self.appRootSelector = self.add(ns.TitleFilenameCombo, name="Application root directory:")
        
    def on_ok(self):
        self.editing=False
        globalSettings = {}
        globalSettings['app_name'] = self.projectName.value
        globalSettings['app_root'] = self.appRootSelector.value
        globalSettings['web_app_name'] = self.projectName.value.lower()
        globalSettings['url_base'] = self.projectName.value.lower()
        globalSettings['app_version'] = self.versionNumber.value

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
        scriptPath = os.path.join(globalSettings['app_root'], globalSettings['static_file_directory'], 'js')
        stylesPath = os.path.join(globalSettings['app_root'], globalSettings['static_file_directory'], 'css')
        xmlPath = os.path.join(globalSettings['app_root'], globalSettings['static_file_directory'], 'xml')
        xslStylesheetPath = os.path.join(globalSettings['app_root'], globalSettings['xsl_stylesheet_directory'])
            
        try:
            ns.notify_confirm(staticFilePath,
                              title="Static Files", form_color='STANDOUT', wrap=True, wide=False, editw=1)
            if not os.path.exists(staticFilePath):
                self.parentApp.directoryManager.addTargetPath(staticFilePath)
                #os.system('mkdir -p %s' % staticFilePath) 

            if not os.path.exists(scriptPath):
                self.parentApp.directoryManager.addTargetPath(scriptPath)

            if not os.path.exists(stylesPath):
                self.parentApp.directoryManager.addTargetPath(stylesPath)

            if not os.path.exists(xmlPath):
                self.parentApp.directoryManager.addTargetPath(xmlPath)
                    
            if not os.path.exists(xslStylesheetPath):
                self.parentApp.directoryManager.addTargetPath(xslStylesheetPath)

            self.parentApp.configManager.initialize(globalSettings)
        except Exception, err:
            ns.notify_confirm(err.message,
                              title="Error",
                              form_color='STANDOUT',
                wrap=True, wide=False, editw=1)

        finally:
            self.parentApp.switchForm('MAIN')

'''
class DataSourceConfigForm(ns.ActionForm):
    def create(self):
        self.sourceNameField = self.add(ns.TitleText, name = 'Enter a name for the datasource')
        self.sourceTypeSelector = self.add(ns.TitleSelectOne,
                                           max_height=4,
                                           value=[1,],
                                           name='Select a datasource type.', values=['menu', 'table'], scroll_exit=True)
        self.tableSelector = self.add(ns.TitleSelectOne, max_height=12, value = [1,], name="Select a database table:",
                values = [], scroll_exit=True)

    def beforeEditing(self):
        self.tableSelector = self.parentApp.activeDatabaseConfig.listTables()
'''

class TableSelectDialog(ns.Popup):
    def __init__(self, *args, **keywords):
        ns.Popup.__init__(self, *args, **keywords)
        self.tables = keywords.get('table_list')
        self.selectedTable = None

    def create(self):
        self.tableSelector = self.add(ns.TitleSelectOne, max_height=-2, value = [1,], name='Select a database table:',
                values = self.tables, scroll_exit=True)

    def exit_editing(self):
        if not len(self.tables):
            return 
        self.selectedTable = self.tables[self.tableSelector.get_value()[0]]

'''
class MenuTypeDataSourceDialog(ns.Popup):
    def __init__(self, *args, **keywords):
        ns.Popup.__init__(self, *args, **keywords)
        self.dataTable = keywords['table']
        self.selectedNameField = ''
        self.selectedValueField = ''


    def create(self):
        columnNames = [column.name for column in self.dataTable.columns] 
        self.nameFieldSelector = self.add(ns.TitleSelectOne, max_height=len(columnNames), value = [1,], name='Name field:',
                values = columnNames, scroll_exit=True)
        
        self.valueFieldSelector = self.add(ns.TitleSelectOne, max_height=len(columnNames), value = [1,], name='Value field:',
                values = columnNames, scroll_exit=True)
'''

'''
class TableTypeDataSourceDialog(ns.Popup):
    def __init__(self, *args, **keywords):
        ns.Popup.__init__(self, *args, **keywords)
        self.dataTable = keywords['table']
        self.selectedFields = []

    def create(self):
        columnNames = [column.name for column in self.dataTable.columns]
        self.fieldSelector = self.add(ns.TitleMultiSelect, max_height =-2, value = [1,], name='Select one or more columns from the source table:',
                values = columnNames, scroll_exit=True)
'''

class DataSourceCreateForm(ns.ActionForm):
    def create(self):
        self.name = 'Create DataSource for UIControls'
        self.sourceTableName = None
        self.dataSourceParameters = []
        self.nameField = self.add(ns.TitleText, name='Data Source name:')
        self.typeSelector = self.add(ns.TitleSelectOne,
                                  name='Data Source type:',
                                  max_height=len(DATASOURCE_TYPE_OPTIONS)*2,
                                  value=[1,], scroll_exit=True, values=DATASOURCE_TYPE_OPTIONS)
        
        self.tableSelectButton = self.add(ns.ButtonPress, name='Select source table')
        self.tableSelectButton.whenPressed = self.selectTable
        self.configureButton = self.add(ns.ButtonPress, name='Configure this DataSource')
        self.configureButton.whenPressed = self.configure
        
    def selectTable(self):
        availableTables = self.parentApp.liveDBInstance.listTables()
        dlg = ns.Popup(name='Database tables')
        tableSelector = dlg.add_widget(ns.TitleSelectOne, max_height=-2, value = [1,], name="Select a source table for the DataSource:",
                values = availableTables, scroll_exit=True)
        dlg.edit()
        self.sourceTableName = availableTables[tableSelector.get_value()[0]]
        

    def configure(self):
        dataSourceType = DATASOURCE_TYPE_OPTIONS[self.typeSelector.value[0]]
        if dataSourceType == 'menu':
            self.configureMenuTypeSource()
        if dataSourceType == 'table':
            self.configureTableTypeSource()
            

    def configureMenuTypeSource(self):
        if self.sourceTableName:
            sourceTable = self.parentApp.liveDBInstance.getTable(self.sourceTableName)
            tableColumns = sourceTable.columns.keys()
            #ns.notify_confirm(dir(tableColumns), title='Message', form_color='STANDOUT', wrap=True, wide=False, editw=1)
            dlg = ns.Popup(name='Configure Menu-type DataSource')
            nameFieldSelector = dlg.add_widget(ns.TitleSelectOne, max_height=-2, value = [1,], name="Name field:",
                values = tableColumns, scroll_exit=True)
            valueFieldSelector = dlg.add_widget(ns.TitleSelectOne, max_height=-2, value = [1,], name="Value field:",
                values = tableColumns, scroll_exit=True)
                           
            dlg.edit()
            self.parameters = []
            self.parameters.append(meta.DataSourceParameter('name_field', tableColumns[nameFieldSelector.get_value()[0]]))
            self.parameters.append(meta.DataSourceParameter('value_field', tableColumns[valueFieldSelector.get_value()[0]]))


    def configureTableTypeSource(self):
        if self.sourceTableName:
            sourceTable = self.parentApp.liveDBInstance.getTable(self.sourceTableName)
            
            availableFields = sourceTable.columns
            dlg = ns.Popup(name='Configure Table-type DataSource')
            fieldSelector = dlg.add_widget(ns.TitleMultiSelect, max_height =-2, value = [1,], name="Select source fields for this DataSource",
                values = availableFields, scroll_exit=True)
            
            dlg.edit()
            self.parameters = []
            fields = []
            selectedItems = fieldSelector.get_selected_values()
            for item in selectedItems:
                fields.append(availableFields[item])
            self.parameters.append(meta.DataSourceParameter('fields',  ','.join(fields)))
            self.parameters.append(meta.DataSourceParameter('table', self.sourceTable.name))
            
            
    def on_ok(self):
        dataSourceType = DATASOURCE_TYPE_OPTIONS[self.typeSelector.get_value()[0]]
        self.dataSourceConfig = meta.DataSourceConfig(dataSourceType, self.parameters)
        alias = self.nameField.value
        self.parentApp.dataSourceManager.addDataSource(self.dataSourceConfig, alias)
        self.parentApp.switchFormPrevious()


class UIControlCreateForm(ns.ActionForm):
    def create(self):
        self.controlNameField = self.add(ns.TitleText, name='Control name:')
        self.controlTypeSelector = self.add(ns.TitleSelectOne, name='Control type:', max_height=4, value = [1,],
                values = UICONTROL_TYPE_OPTIONS, scroll_exit=True)

        self.dataSourceAlias = ''
        self.dataSourceLabel = self.add(ns.TitleFixedText, name='Datasource name:', value='')
        self.selectDataSourceButton = self.add(ns.ButtonPress, name='Select a Datasource')
        self.selectDataSourceButton.whenPressed = self.selectDataSource


    def selectDataSource(self):   
        dataSources = self.parentApp.dataSourceManager.listDataSources()  
        if not len(dataSources):
            self.parentApp.switchForm('DATASOURCE_CREATE')
        else:
            dlg = ns.Popup(name='Data Sources')
            sourceSelector = dlg.add_widget(ns.TitleSelectOne, name='Select a datasource:', max_height=len(dataSources)+2, value = [1,],
                values = dataSources, scroll_exit=True)
            dlg.edit()
            self.dataSourceAlias = dataSources[sourceSelector.value[0]]
            self.dataSourceLabel.value = self.dataSourceAlias
        self.display()

    def on_ok(self):
        controlName = self.controlNameField.value
        dataSourceName = self.dataSourceAlias
        controlType = UICONTROL_TYPE_OPTIONS[self.controlTypeSelector.value[0]]
        newControlCfg = meta.ControlConfig(controlType, controlName, self.dataSourceAlias)
        
        self.parentApp.switchForm('MAIN')
        

    def beforeEditing(self):
        pass
        '''
        if not len(self.parentApp.dataSourceManager.listDataSources()):
            self.selectDataSourceButton.name = 'Create new DataSource...'
        else:            
            self.dataSourceSelector.values = self.parentApp.dataSourceManager.listDataSources()
        ''' 
            


class UIControlConfigForm(ns.ActionForm):
    def create(self):       
        self.createControlButton = self.add(ns.ButtonPress, name='Create a custom data-bound HTML control')
        self.browseControlsButton = self.add(ns.ButtonPress, name='Browse existing HTML controls')
        self.autoCreateButton = self.add(ns.ButtonPress, name='Auto-create HTML select controls from lookup tables')

        self.createControlButton.whenPressed = self.createControl
        self.browseControlsButton.whenPressed = self.browseControls
        self.autoCreateButton.whenPressed = self.autoCreateControls


    def createControl(self):
        self.parentApp.switchForm('UICONTROL_CREATE')


    def browseControls(self):
        ns.notify_confirm('Browse UIcontrols.', title='Message', form_color='STANDOUT', wrap=True, wide=False, editw=1)


    def autoCreateControls(self):
        ns.notify_confirm('Auto-create UIcontrols.', title='Message', form_color='STANDOUT', wrap=True, wide=False, editw=1)


'''
class VirtualEnvMenuForm(ns.ActionForm):
    def create(self):
        self.virtualEnvHome = ''
        self.virtualEnvSelector = self.add(ns.TitleSelectOne,
                                           max_height=12,
                                           value = [1,],
                                           name="Select a virtual environment for your Serpentine app:",
                                           values = [], scroll_exit=False)

    def beforeEditing(self):
        self.virtualEnvHome = os.environ.get('WORKON_HOME')
        self.environments = []
        fileList = os.listdir(self.virtualEnvHome)
        for f in fileList:
            if os.path.isdir(os.path.join(self.virtualEnvHome, f)):
                self.environments.append(f)

        self.virtualEnvSelector.values = self.environments
        self.virtualEnvSelector.set_value(0)

    def on_ok(self):
        selectedEnv = self.environments[self.virtualEnvSelector.value[0]]
        pyVersions = os.listdir(os.path.sep.join([self.virtualEnvHome, selectedEnv, 'lib']))
        
        self.parentApp.pythonVersions = pyVersions
        self.parentApp.switchForm('MAIN')
        #siteDirLocation = os.path.sep.join([virtualEnvHome, selectedEnv, 'lib', pythonVersion, 'site-packages'])
'''     

        

class SiteDirConfigForm(ns.ActionForm):
    
    def create(self):
        self.checkboxAnswers = ['Yes', 'No']
        
        self.usingVirtualEnvWrapperCheckbox = self.add(ns.TitleSelectOne, max_height=4, value = [1,], name="Are you using virtualenvwrapper?",
                values = self.checkboxAnswers, scroll_exit=True)
        self.add(ns.FixedText, value='( If you are NOT using virtualenvwrapper, please select your Python site directory below. )')
        self.siteDirSelector = self.add(ns.TitleFilenameCombo, name='Python site directory:')

    def on_cancel(self):
        self.editing = False
        self.parentApp.switchForm('MAIN')

    def on_ok(self):
        isUsingVirtualEnvWrapper = self.checkboxAnswers[self.usingVirtualEnvWrapperCheckbox.value[0]]
        if isUsingVirtualEnvWrapper == 'Yes':
            virtualEnvHome = os.environ.get('WORKON_HOME')
            environments = []
            fileList = os.listdir(virtualEnvHome)
            for f in fileList:
                if os.path.isdir(os.path.join(self.virtualEnvHome, f)):
                    environments.append(f)
            dlg = ns.Popup(name='Select Python Virtual Environment')
            virtualEnvSelector = ns.add_widget(ns.TitleSelectOne,
                                           max_height=12,
                                           value = [1,],
                                           name="Select the virtualenv you will use for this app:",
                                           values = environments, scroll_exit=False)
            virtualEnvSelector.set_value(0)
            dlg.edit()
            selectedEnv = environments[virtualEnvSelector.value[0]]
            pyVersions = os.listdir(os.path.sep.join([virtualEnvHome, selectedEnv, 'lib']))
            
            self.parentApp.pythonVersions = {selectedEnv: pyVersions}
            
        else:
            siteDirLocation = self.siteDirSelector.value
            self.parentApp.pythonSiteDir = siteDirLocation
            self.parentApp.switchForm('MAIN')

'''
        self.virtualEnvHome = os.environ.get('WORKON_HOME')
        self.environments = []
        fileList = os.listdir(self.virtualEnvHome)
        for f in fileList:
            if os.path.isdir(os.path.join(self.virtualEnvHome, f)):
                self.environments.append(f)

        self.virtualEnvSelector.values = self.environments
        self.virtualEnvSelector.set_value(0)

    def on_ok(self):
        selectedEnv = self.environments[self.virtualEnvSelector.value[0]]
        pyVersions = os.listdir(os.path.sep.join([self.virtualEnvHome, selectedEnv, 'lib']))
        
        self.parentApp.pythonVersions = pyVersions
        self.parentApp.switchForm('MAIN')
        #siteDirLocation = os.path.sep.join([virtualEnvHome, selectedEnv, 'lib', pythonVersion, 'site-packages'])
'''    



class ModelConfigForm(ns.ActionForm):
    def create(self):
        self.canSelectTables = False
        self.value = None
        self.name = 'Model Configuration'
        self.tableSelector = self.add(ns.TitleMultiSelect, max_height =-2, value = [1,], name="Select One Or More Tables",
                values = [], scroll_exit=False)


    def beforeEditing(self):        
        dbConfigAlias = self.parentApp.activeDatabaseConfigAlias
        if not dbConfigAlias:
            ns.notify_confirm('In order to configure models, first create a valid database configuration.',
                              title="Message", form_color='STANDOUT', wrap=True, wide=False, editw=1)            
        else:
            try:
                # There must be a live database connection
                dbInstance = self.parentApp.getDBInstance(dbConfigAlias)                
                ns.notify_confirm('Connected to database using config %s.' % dbConfigAlias,
                                  title='Success', form_color='STANDOUT', wrap=True, wide=False, editw=1)
                self.tableSelector.values = dbInstance.listTables()
                self.canSelectTables = True
            except Exception, err:
                ns.notify_confirm(err.message, title='Error', form_color='STANDOUT', wrap=True, wide=False, editw=1)
                

    def display(self, **kwargs):
        if self.canSelectTables:
            ns.ActionForm.display(self, kwargs)
        else:
            self.editing = False
            self.parentApp.switchForm('MAIN')


    def on_ok(self):
        dbInstance = self.parentApp.getDBInstance(self.parentApp.activeDatabaseConfigAlias)
        for tblName in self.tableSelector.get_selected_objects():
            self.parentApp.modelManager.addTable(dbInstance.getTable(tblName))
        self.parentApp.switchForm('MAIN')

    def on_cancel(self):
        self.parentApp.switchForm('MAIN')

    

class DatabaseConfigForm(ns.ActionForm):
    def create(self):
        self.value = None
        self.name = 'Database Configuration'
        self.hostnameField = self.add(ns.TitleText, name = "Host where database resides:", default = "localhost")
        self.schemaField = self.add(ns.TitleText, name = "Enter database schema:", default = "schema")
        self.usernameField = self.add(ns.TitleText, name = "Enter database username:")
        self.passwordField = self.add(ns.TitlePassword, name = "Enter database password:")
        self.dbConfigNameField = self.add(ns.TitleText, name = "Enter a name for this database configuration:", default = "localhost.schema" )

    def loadDBConfig(self, dbConfig):
        self.hostnameField.value = dbConfig.host
        self.schemaField.value = dbConfig.schema
        self.usernameField.value = dbConfig.username
        self.passwordField.value = dbConfig.password


    def populateDBConfig(self):
        host = self.hostnameField.value
        schema = self.schemaField.value
        username = self.usernameField.value
        password = self.passwordField.value
        return meta.DatabaseConfig(host, schema, username, password)

    def clearAllFields(self):
        self.hostnameField.value = ''
        self.schemaField.value = ''
        self.usernameField.value = ''
        self.passwordField.value = ''
        self.dbConfigNameField.value = ''

    def beforeEditing(self):
        dbcfg = self.parentApp.activeDatabaseConfig
        if dbcfg:
            self.loadDBConfig(dbcfg)
        else:
            self.clearAllFields()
                        
    def on_ok(self):
        self.parentApp.addDatabaseConfig(self.populateDBConfig(), self.dbConfigNameField.value)
        #ns.notify_confirm(str(self.parentApp.listDatabaseConfigs()), title="Message", form_color='STANDOUT', wrap=True, wide=False, editw=0)
        self.parentApp.switchForm('MAIN')

    def on_cancel(self):
        self.parentApp.switchForm('MAIN')



class DatabaseConfigMenuForm(ns.ActionForm):
    def create(self):
        self.value = None
        self.name = 'sconfig: Database config select'
        configOptions = self.parentApp.listDatabaseConfigs()
        self.selector = self.add(ns.TitleSelectOne, max_height=4, value = [1,], name="Select a database configuration to modify:",
                values = [], scroll_exit=True)

    def beforeEditing(self):
        self.selector.values = self.parentApp.listDatabaseConfigs()

    def on_ok(self):
        self.editing = False
        selectedAlias = self.selector.get_selected_objects()[0]
        #ns.notify_confirm(str(self.selector.get_selected_objects()), title="Message", form_color='STANDOUT', wrap=True, wide=False, editw=0)
        self.parentApp.selectDatabaseConfig(selectedAlias)
        self.parentApp.switchForm('DB_CONFIG')

    def on_cancel(self):
        self.editing = False;
        self.parentApp.switchForm('MAIN')


class DBConfigSelectDialog(ns.Popup):
    def __init__(self, *args, **keywords):
        ns.Popup.__init__(self, *args, **keywords)
        self.configList = None

    def create(self):
        self.configSelector = self.add(ns.TitleSelectOne, max_height=-2, value=[1,], name='Select a database config:', values=self.configList, scroll_exit=True)
        


class MainForm(ns.ActionFormWithMenus):
    def create(self):
        self.value = None
        self.name =  "::: sconfig: Serpentine Configuration Tool :::"
        
        self.appNameField = self.add(ns.TitleFixedText, name = "Application name:")
        self.versionField = self.add(ns.TitleFixedText, name = "Version number:")
        self.pythonVersionSelector = self.add(ns.TitleSelectOne, max_height=4, value = [0,], name='Python environment:', values = [], scroll_exit= True)
        self.appRootField = self.add(ns.TitleFixedText, name= 'Application root directory:')
       

        self.loadConfigFileButton = self.add(ns.ButtonPress, name='Load existing configuration file...')
        self.loadConfigFileButton.whenPressed = self.loadConfigFile
        
        self.dbConnectButton = self.add(ns.ButtonPress, name='Connect to database...')        
        self.dbConnectButton.whenPressed = self.connectToDB
        
        self.sectionMenu = self.new_menu('Config Section')
        self.sectionMenu.addItem(text='Python site directory', onSelect=self.configurePythonSiteDir, shortcut=None, arguments=None, keywords=None)
        self.sectionMenu.addItem(text='Global Settings', onSelect=self.configureGlobals, shortcut=None, arguments=None, keywords=None)        
        self.sectionMenu.addItem(text='Add Database Config', onSelect=self.configureNewDatabase, shortcut=None, arguments=None, keywords=None)
        self.sectionMenu.addItem(text='Edit Database Config', onSelect=self.editDatabase, shortcut=None, arguments=None, keywords=None)    
        self.sectionMenu.addItem(text='Models', onSelect=self.configureModels, shortcut=None, arguments=None, keywords=None)
        self.sectionMenu.addItem(text='Views', onSelect=None, shortcut=None, arguments=None, keywords=None)
        self.sectionMenu.addItem(text='UI Controls', onSelect=self.manageUIControls, shortcut=None, arguments=None, keywords=None)
        self.sectionMenu.addItem(text='Plugins', onSelect=None, shortcut=None, arguments=None, keywords=None)
        #self.editing = True


    def connectToDB(self):
        availableDBConfigs = self.parentApp.listDatabaseConfigs()
        if not len(availableDBConfigs):
            self.parentApp.switchForm('DB_CONFIG')
        else:
            dlg = ns.Popup(name='Select a database config alias')
            configSelector = dlg.add_widget(ns.TitleSelectOne, max_height=-2, value = [1,], name="Available configs:",
                values = availableDBConfigs, scroll_exit=True)
            dlg.edit()
            selectedConfigAlias = availableDBConfigs[configSelector.get_value()[0]]
            self.parentApp.connectToDB(selectedConfigAlias)
            

    def loadConfigFile(self):
        dlg = ns.Popup(name='Load a Serpentine configuration file')
        configFileSelect = dlg.add_widget(ns.TitleFilenameCombo, name="Load file")
        dlg.edit()
        # TODO: actually load selected config file
        

    def configureGlobals(self):
        self.parentApp.switchForm('GLOBAL_CONFIG')

    def configurePythonSiteDir(self):
        self.parentApp.switchForm('SITE_DIR_CONFIG')

    def configureNewDatabase(self):
        self.parentApp.switchForm("DB_CONFIG")

    def editDatabase(self):
        self.parentApp.switchForm('DB_CONFIG_MENU')   

    def configureModels(self):
        self.parentApp.switchForm('MODEL_CONFIG')

    def manageUIControls(self):        
        self.parentApp.switchForm('UICONTROL_CONFIG')
    
    def beforeEditing(self):
        self.appNameField.value = self.parentApp.configManager.getAppName()
        self.versionField.value = self.parentApp.configManager.getAppVersion()
        self.appRootField.value = self.parentApp.configManager.getAppRoot()
        self.pythonVersionSelector.values = self.parentApp.pythonVersions.keys()
        if len(self.pythonVersionSelector.values) and not self.pythonVersionSelector.get_selected_objects():
            self.pythonVersionSelector.set_value(0)
        
    def on_ok(self):
        self.parentApp.setNextForm(None)   


class ContentManager(object):
    def __init__(self, templatePath):
        self.j2Environment = jinja2.Environment(loader = jinja2.FileSystemLoader(templatePath), 
                                                    undefined = StrictUndefined, cache_size=0)
        self.templateManager = content.JinjaTemplateManager(j2Environment)

        


class ModelManager(object):
    def __init__(self):
        self.tableSet = set()
        
    def listTables(self):
        return [table.name for table in self.tableSet]

    def addTable(self, table):
        self.tableSet.add(table)
        
        
    def createModelTableMap(self):
        modelTableMap = {}
        for table in self.tableSet:
            modelName = self.convertTableNameToModelName(table.name)
            modelTableMap[modelName] = meta.ModelConfig(modelName, table, None)

        return modelTableMap


    def generateModelClasses(self, configPackage):
        """Generate all boilerplate Model classes, in a single module

        Arguments: 
        modelNames -- an array of model names
        """     
        modelPkg = os.path.join("build", "%s.py" % configPackage.default_model_package) 
        with open(modelPkg, "a") as f:        
            for modelName in configPackage.models:
                f.write("\nclass %s(object): pass" % modelName)
                f.write("\n\n")


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
              factory = meta.FieldConfigFactory()
              for modelName in modelTableMap:                  
                  # formspecs need the URL base to properly generate action URLs in the HTML templates
                  newFormConfig = meta.FormConfig(modelName, environment.getURLBase()) 
                  modelConfig = modelTableMap[modelName]

                  table = modelConfig.table
                  
                  for column in table.columns:
                      newFormConfig.addField(factory.create(column))

                  formConfigs.append(newFormConfig)
                  
              return formConfigs
          finally:
              pass


class DataSourceManager(object):
    def __init__(self):
        self.datasources = {}


    def addDataSource(self, dataSource, alias):
        self.datasources[alias] = dataSource

    def listDataSources(self):
        return self.datasources.keys()


    def getDataSource(self, alias):
        source =  self.datasources.get(alias)
        if not source:
            raise NoSuchDataSourceException(alias)
        return source


    def getDatasourceAliasesForControlType(self, controlTypeName):
        result = []
        for key in self.datasources:
            dataSourceConfig = self.datasources[key]
            if dataSourceConfig.type == controlTypeName:
                result.append(key)

        return result



class ConfigManager(object):
    def __init__(self):
        self.configPackage = None
        self.environment = None
        
    def initialize(self, settings):
        self.environment = env.Environment()
        self.environment.importGlobalSettings(settings)          
        configPackage = sconfig.ConfigurationPackage(self.environment)
        
    def getAppName(self):
        if self.environment:
            return self.environment.getAppName()
        return ''

    def getAppVersion(self):
        if self.environment:
            return self.environment.getAppVersion()
        return ''

    def getAppRoot(self):
        if self.environment:
            return self.environment.getAppRoot()
        return ''


class FormSpecManager(object):
    def __init__(self):
        self.formSpecs = []

    def listFormSpecNames(self):
        return [str(spec) for spec in self.formSpecs]

    def getFormSpecs(self):
        return self.formSpecs

    def clearFormSpecs(self):
        self.formSpecs = []
    
    def createFormSpecsFromModelTableMap(self, modelTableMap):        
        
        factory = meta.FieldConfigFactory()
        for modelName in modelTableMap.keys():                  
            # formspecs need the URL base to properly generate action URLs in the HTML templates
            newFormConfig = meta.FormConfig(modelName, environment.getURLBase()) 
            modelConfig = modelTableMap[modelName]

            table = modelConfig.table
                  
            for column in table.columns:
                newFormConfig.addField(factory.create(column))

            self.formSpecs.append(newFormConfig)

                  
class UIControlManager(object):
    def __init__(self):
        self.uiControlConfigs = {}

    def addUIControl(self, uiControlConfig):
        self.uiControlConfigs[uiControlConfig.name] = uiControlConfig
        
    def listUIControls(self):
        return self.uiControlConfigs.keys()

    def clearUIControls(self):
        self.uiControlConfigs = {}


    def getUIControlConfiguration(self, alias):
        cfg = self.uiControlConfigs.get(alias)
        if not cfg:
            raise NoSuchControlConfigException(alias)
        return cfg

class DirectoryManager(object):
    def __init__(self):
        self.directoriesToCreate = []

    def addTargetPath(self, directoryPath):
        self.directoriesToCreate.append(directoryPath)

    def reset(self):
        self.directoriesToCreate = []

    def listTargetPaths(self):
        return self.directoriesToCreate

    def createTargets(self):
        for path in self.directoriesToCreate:
            os.system('mkdir -p %s' % path)
    

class SConfigApp(ns.NPSAppManaged):
    def addDatabaseConfig(self, config, alias):
        self.databaseConfigTable[alias] = config
        self.activeDatabaseConfigAlias = alias

                
    def listDatabaseConfigs(self):
        return self.databaseConfigTable.keys()


    def selectDatabaseConfig(self, alias):
        self.activeDatabaseConfigAlias = alias

    @property
    def activeDatabaseConfig(self):
        if not self.activeDatabaseConfigAlias:
            return None
        return self.databaseConfigTable.get(self.activeDatabaseConfigAlias)

    def connectToDB(self, dbConfigAlias):
        dbConfig = self.databaseConfigTable.get(dbConfigAlias)
        if not dbConfig:
            raise Exception('No configuration alias "%s" has been registered.' % dbConfigAlias)
        
        dbInstance = db.MySQLDatabase(dbConfig.host, dbConfig.schema)            
        dbInstance.login(dbConfig.username, dbConfig.password)
        self.activeDatabaseConfigAlias = dbConfigAlias
        self.liveDBInstance = dbInstance

    def getDBInstance(self, dbConfigAlias):
        if not self.liveDBInstance:                    
            self.connectToDB(dbConfigAlias)
        elif dbConfigAlias != self.activeDatabaseConfigAlias:
            self.connectToDB(dbConfigAlias)
            
        return self.liveDBInstance

    
    def onStart(self):
        self.modelManager = ModelManager()
        self.configManager = ConfigManager()
        self.directoryManager = DirectoryManager()
        self.dataSourceManager = DataSourceManager()
        self.uiControlManager = UIControlManager()
        
        self.databaseConfigTable = {}
        self.activeDatabaseConfigAlias = ''
        self.liveDBInstance = None
        self.pythonVersions = []
        self.dataSourceNames = ['source1', 'source2', 'source3']
        
        self.addForm('MAIN', MainForm)
        self.addForm('DB_CONFIG', DatabaseConfigForm)
        self.addForm('DB_CONFIG_MENU', DatabaseConfigMenuForm)        
        self.addForm('GLOBAL_CONFIG', GlobalSettingsForm)
        self.addForm('SITE_DIR_CONFIG', SiteDirConfigForm)
        self.addForm('MODEL_CONFIG', ModelConfigForm)
        #self.addForm('VIRTUAL_ENV_SELECT', VirtualEnvMenuForm)
        self.addForm('UICONTROL_CREATE', UIControlCreateForm)
        self.addForm('UICONTROL_CONFIG', UIControlConfigForm)        
        self.addForm('DATASOURCE_CREATE', DataSourceCreateForm)

        # For testing only
        newConfig = meta.DatabaseConfig('localhost', 'blocpower', 'dtaylor', 'notobvious')
        self.addDatabaseConfig(newConfig, 'db01')
        

class TestApp(ns.NPSApp):
    def main(self):
        # These lines create the form and populate it with widgets.
        # A fairly complex screen in only 8 or so lines of code - a line for each control.
        mainForm  = ns.Form(name = "Welcome to SConfig",)
        title  = mainForm.add(ns.TitleText, name = "::: Serpentine Config Tool :::",)
        fn = mainForm.add(ns.TitleFilename, name = "Filename:")
        fn2 = mainForm.add(ns.TitleFilenameCombo, name="Filename2:")
        dt = mainForm.add(ns.TitleDateCombo, name = "Date:")
        s  = mainForm.add(ns.TitleSlider, out_of=12, name = "Slider")
        ml = mainForm.add(ns.MultiLineEdit,
               value = """try typing here!\nMutiline text, press ^R to reformat.\n""",
               max_height=5, rely=9)
        ms = mainForm.add(ns.TitleSelectOne, max_height=4, value = [1,], name="Pick One",
                values = ["Option1","Option2","Option3"], scroll_exit=True)
        ms2= mainForm.add(ns.TitleMultiSelect, max_height =-2, value = [1,], name="Pick Several",
                values = ["Option1","Option2","Option3"], scroll_exit=True)

        # This lets the user interact with the Form.
        mainForm.edit()

        print(ms.get_selected_objects())
        print(ml.value)


if __name__ == "__main__":
    #App = TestApp()
    App = SConfigApp()
    
    App.run()
