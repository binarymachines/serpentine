#!/usr/bin/python

import os, sys
import db
import time
import curses, traceback
import curses.wrapper
from StringIO import StringIO

import jinja2
from content import JinjaTemplateManager
from wtforms import *
from lxml import etree
from sqlalchemy import *

from cli import *


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
            
            self.app_root = None
            self.static_file_path = None
            self.default_forms_package = None
            self.default_model_package = None
            self.default_controller_package = None
            self.default_helper_package = None
            self.startup_db = None
            self.url_base = None
            self.template_path = None
            self.stylesheet_path = None
            self.dependency_path = None
            self.config_filename = None

            self.models = {}
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

          currentDir = os.getcwd()
          bootstrapDir = os.path.join(currentDir, "bootstrap")
          env = jinja2.Environment(loader = jinja2.FileSystemLoader(bootstrapDir))
          templateMgr = JinjaTemplateManager(env)

          

          tableList = self.selectTables(screen)
          # TODO: Add parent-child mapping selection logic

          modelTableMap = self.createModelTableMap(tableList)

          self.generateModelCode(modelTableMap.keys())
          formSpecArray = self.createFormSpecs(modelTableMap)

          # some frames will have helper functions
          self.designateHelperFunctions(formSpecArray, screen)

          self.generateControllerCode(formSpecArray, templateMgr)
          self.generateApplicationTemplates(formSpecArray, templateMgr)
          self.generateFormCode(formSpecArray, templateMgr)
          
          # now generate the config file

          configFile = None
          try:
              configFileTemplate = templateMgr.getTemplate("config_template.tpl")
              configFilename = "%s.conf" % self.projectName.lower()
              configFile = open(os.path.join("bootstrap", configFilename), "w")
              configFile.write(configFileTemplate.render(config = self))
              configFile.close()
              self.config_filename = configFilename
          finally:
              if configFile is not None:
                  configFile.close()
      
      def designateHelperFunctions(self, formSpecs, screen):
          """Allow the user to specify a helper function for one or more frames"""

          pass


      

      def setupDatabases(self, screen):
          """Allow the user to specify one or more named database instances from which to select later"""

          options = ["Create new database", "List databases"]

          prompt = MenuPrompt(Menu(options), "Select an option from the menu.")
          
          while not prompt.escaped:
              selection = prompt.show(screen)
              if prompt.escaped:
                  break
              if prompt.selectedIndex == 1:
                  schema = TextPrompt("Enter database schema", None).show(screen)
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


            projectNamePrompt = TextPrompt("Enter project name", None)
            self.projectName = projectNamePrompt.show(screen)
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
                       
            self.default_forms_package = '%s_forms' % self.projectName.lower()
            self.default_model_package = '%s_models' % self.projectName.lower()
            self.default_controller_package = '%s_controllers' % self.projectName.lower()
            self.default_helper_package = '%s_helpers' % self.projectName.lower()
            
            try:
                os.system('mkdir %s' % self.static_file_path) 
                #os.system('mkdir %s' % self.template_path)
                os.system('mkdir %s' % self.stylesheet_path)
                os.system('mkdir %s' % os.path.join(scriptPath[0], scriptPath[1]))
                os.system('mkdir %s' % os.path.join(stylesPath[0], stylesPath[1]))
                os.system('mkdir %s' % os.path.join(xmlPath[0], xmlPath[1]))
            except IOError, err:
                raise err

            self.globalDataInitialized = True
            

      def selectTables(self, screen):
      
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
                prompt = MultipleChoiceMenuPrompt(m, 'Select one or more database tables to add to your application model.')
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
      
      def generateFormCode(self, formSpecs, templateManager):
          """Create the WTForms Form instances for the application under construction

          Arguments:
          formSpecs -- an array of FormSpec instances
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

          # First, transform the XML seed template into a FormSpec XML document.

          xmlHandle = None
          xmlTemplate = templateManager.getTemplate("formspec_xml.tpl")
          xmlFile = None
          htmlFile = None

          generatedFiles = {}
          try:
              for fSpec in formSpecs:
                  
                  # Use each FormSpec object in our list to populate the model XML template
                  # and create an XML representation of the FormSpec.
                  #
                  xmlHandle = StringIO(xmlTemplate.render(formspec=fSpec))

                  # the raw xml text now resides in the file-like string object xmlHandle

                  # write it to a file with the same name as the underlying Model; 
                  # i.e., for the Widget formspec the file would be Widget.xml
                  #
                  xmlFilename = os.path.join("bootstrap", "%s.xml" % fSpec.model.lower())
                  xmlFile = open(xmlFilename, "w") 
                  xmlFile.write(xmlHandle.getvalue())
                  xmlFile.close()

                  # Next, transform the FormSpec document into a set of final HTML templates.
                  # The resulting templates will become views in the live application.
                  #
                  # parse the text and create a DOM tree
                  formSpecXML = etree.parse(xmlHandle)

                  # index template, for viewing all objects of a given type
                  xslFilename = os.path.join("bootstrap", "index_template.xsl")
                  xslTree = etree.parse(xslFilename)
                  indexTemplateTransform = etree.XSLT(xslTree)
                  indexTemplateHTMLDoc = indexTemplateTransform(formSpecXML)
                  
                  indexFilename = os.path.join("bootstrap", "index_%s.html" % fSpec.model.lower())
                  htmlFile = open(indexFilename, "w")   
                  htmlFile.write(etree.tostring(indexTemplateHTMLDoc, pretty_print=True))
                  htmlFile.close()

                  indexFrameAlias = "%s_list" % fSpec.model.lower()
                  
                  self.frames[indexFrameAlias] = FrameConfig(indexFrameAlias, indexFilename, fSpec.formClassName, "html")
                  
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

                  insertFilename = os.path.join("bootstrap", "insert_%s.html" % fSpec.model.lower())

                  htmlFile = open(insertFilename, "w")  
                  htmlFile.write(etree.tostring(insertHTMLDoc, pretty_print = True))
                  htmlFile.close()

                  insertFrameAlias = "%s_insert" % fSpec.model.lower()

                  self.frames[insertFrameAlias] = FrameConfig(insertFrameAlias, insertFilename, fSpec.formClassName, "html")

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

                  updateFilename = os.path.join("bootstrap", "update_%s.html" % fSpec.model.lower())

                  htmlFile = open(updateFilename, "w")  
                  htmlFile.write(etree.tostring(updateHTMLDoc, pretty_print = True))
                  htmlFile.close()

                  updateFrameAlias = "%s_update" % fSpec.model.lower()

                  self.frames[updateFrameAlias] = FrameConfig(updateFrameAlias, updateFilename, fSpec.formClassName, "html")

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
        self.typeMap = { "BOOL": BooleanField, "INTEGER": IntegerField, "FLOAT": DecimalField, "DOUBLE": DecimalField, "DATE": DateField, "DATETIME": DateTimeField,
                             "INTEGER": IntegerField, "TINYINT": IntegerField, "VARCHAR": TextField }
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
           
    
def main():
        display = CursesDisplay(SConfigurator)
        display.open()
        
       
                
            
if __name__ == "__main__":
        main() 
    
    
    
            
            

      
