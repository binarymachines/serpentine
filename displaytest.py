#!/usr/bin/python


import npyscreen as ns
import curses

import db
from metaobjects import *
import environment as env



'''
class PopupMenu(BoxBasic):
    _contained_widget = ns.TitleSelectOne

    def
    def create(self):
        self._contained_widget.value
'''

class GlobalSettingsForm(ns.Form):
    def create(self):
        self.value = None
        self.projectName  = self.add(ns.TitleText, name = "Project name:")
        self.versionNumber = self.add(ns.TitleText, name = "Version number:")

        
    def on_ok(self):
        self.editing=False
        globalSettings = {}
        globalSettings['app_name'] = self.projectName.value
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
            
        staticFilePath = os.path.join(globalSettings['app_root'], 'deploy', globalSettings['static_file_directory'])
        scriptPath = os.path.join(globalSettings['app_root'], 'deploy', globalSettings['static_file_directory'], 'js')
        stylesPath = os.path.join(globalSettings['app_root'], 'deploy', globalSettings['static_file_directory'], 'css')
        xmlPath = os.path.join(globalSettings['app_root'], 'deploy', globalSettings['static_file_directory'], 'xml')
        xslStylesheetPath = os.path.join(globalSettings['app_root'], 'deploy', globalSettings['xsl_stylesheet_directory'])
            
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
            
        except IOError, err:
            raise err

        self.parentApp.globalSettings = globalSettings
        self.parentApp.switchForm('MAIN')


class ModelConfigForm(ns.ActionForm):
    def create(self):
        self.value = None
        self.name = 'Model Configuration'
        self.tableSelector = self.add(ns.TitleMultiSelect, max_height =-2, value = [1,], name="Select One Or More Tables",
                values = ["Option1","Option2","Option3"], scroll_exit=False)


        
    def beforeEditing(self):
        # There must be a live database connection
        dbcfg = self.parentApp.activeDatabaseConfig
        if not dbcfg:
            ns.notify_confirm('In order to configure models, first connect to the database.', title="Message", form_color='STANDOUT', wrap=True, wide=False, editw=1)
            self.parentApp.switchForm('MAIN')
        else:
            # connect
            #self.parentApp.environment.importDatabaseSettings({dbConfigName: newConfig})
            #configPackage.addDatabaseConfig(newConfig, dbConfigName)
            dbInstance = db.MySQLDatabase(dbcfg.host, dbcfg.schema)
            dbInstance.login(dbConfig.username, dbConfig.password)
            return dbInstance
            

    def on_ok(self):
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
        return DatabaseConfig(host, schema, username, password)

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


class MainForm(ns.ActionFormWithMenus):
    def create(self):
        self.value = None
        self.name =  "::: sconfig: Serpentine Configuration Tool :::"

        self.appNameField = self.add(ns.TitleText, name = "Application name:",)
        self.versionField = self.add(ns.TitleText, name = "Version number:",)
        
        self.configFileSelect = self.add(ns.TitleFilenameCombo, name="Load existing configuraton file:")
        self.configFileSelect.add_handlers({curses.ascii.ESC:  self.configFileSelect.h_exit_escape})
        
        self.sectionMenu = self.new_menu('Config Section')
        #self.sectionMenu.addItem(text='Global Settings', onSelect=None, shortcut=None, arguments=None, keywords=None)
        
        self.sectionMenu.addItem(text='Add Database Config', onSelect=self.configureNewDatabase, shortcut=None, arguments=None, keywords=None)
        self.sectionMenu.addItem(text='Edit Database Config', onSelect=self.editDatabase, shortcut=None, arguments=None, keywords=None)
        
        self.sectionMenu.addItem(text='Models', onSelect=self.configureModels, shortcut=None, arguments=None, keywords=None)
        self.sectionMenu.addItem(text='Views', onSelect=None, shortcut=None, arguments=None, keywords=None)
        self.sectionMenu.addItem(text='UI Controls', onSelect=None, shortcut=None, arguments=None, keywords=None)
        self.sectionMenu.addItem(text='Plugins', onSelect=None, shortcut=None, arguments=None, keywords=None)
        #self.editing = True

        
    def configureNewDatabase(self):
        self.parentApp.switchForm("DB_CONFIG")

    def editDatabase(self):
        self.parentApp.switchForm('DB_CONFIG_MENU')

    def configureGlobals(self):
        self.parentApp.switchForm('GLOBAL_CONFIG')

    def configureModels(self):
        self.parentApp.switchForm('MODEL_CONFIG')
    '''
    def afterEditing(self):
        self.parentApp.setNextForm(None)    
        
    '''
    def on_ok(self):
        self.parentApp.setNextForm(None)   
    


class SConfigApp(ns.NPSAppManaged):
    def addDatabaseConfig(self, config, alias):
        self.databaseConfigTable[alias] = config
        
    def listDatabaseConfigs(self):
        return self.databaseConfigTable.keys()


    def selectDatabaseConfig(self, alias):
        self.activeDatabaseConfigAlias = alias

    @property
    def activeDatabaseConfig(self):
        if not self.activeDatabaseConfigAlias:
            return None
        return self.databaseConfigTable.get(self.activeDatabaseConfigAlias)
        
    
    def onStart(self):
        self.databaseConfigTable = {}
        self.activeDatabaseConfigAlias = ''
        self.environment = env.Environment()
        self.configPackage = None
        
        self.addForm('MAIN', MainForm)
        self.addForm('DB_CONFIG', DatabaseConfigForm)
        self.addForm('DB_CONFIG_MENU', DatabaseConfigMenuForm)
        self.addForm('GLOBAL_CONFIG', GlobalSettingsForm)
        self.addForm('MODEL_CONFIG', ModelConfigForm)

        
        
        

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
