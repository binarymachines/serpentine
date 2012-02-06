#
#------ Content & Templating module --------
#

import os
import os.path
import exceptions
import sys

import jinja2

import wtforms
from wtforms import HiddenField, validators

from sqlalchemy.sql.expression import select

from lxml import etree
from StringIO import *

from core import *
from environment import *

import logging
logging.basicConfig(filename = 'serpentine.log', level = logging.INFO, format = "%(asctime)s - %(message)s")

log = logging.info



class MissingDataSourceParameterError(Exception):
    def __init__(self, dataSourceClass, requiredParameterArray):
        message = '%s init call is missing one or more of the following required params: %s' \
        % (dataSourceClass.__name__, requiredParameterArray)
        Exception.__init__(self, message)



class JinjaTemplateManager:
    def __init__(self, environment):
        self.environment = environment
        
    def getTemplate(self, filename):
        return self.environment.get_template(filename)
        


class DisplayManager:
    def __init__(self, stylesheetPath):
        self.stylesheetMap = {}
        self.stylesheetPath = stylesheetPath
        self.rawXSLFiles = {}
        
        env = jinja2.Environment(loader = jinja2.FileSystemLoader(stylesheetPath))

        # this is so that we can factor out common elements in our XSL stylesheets
        # via Jinja2 template inheritance. When an XSL transform is called for, 
        # we will first render the requested XSL document as a Jinja template,
        # then apply the resulting XSL to the passed XML.
        
        self.j2TemplateMgr = JinjaTemplateManager(env)
    
    def assignStylesheet(self, xslFilename, frameID, channelID=None, **kwargs):

        # first, load the stylesheet as a Jinja template
        xslHandle = None
        try:
            xslTemplateObject = self.j2TemplateMgr.getTemplate(xslFilename)
            
            # resolve the Jinja tags in the template, place result in a file-like string object
            xslHandle = StringIO(xslTemplateObject.render())
        
            # now use the resolved XSL (which should have no more Jinja tags)
            # as a valid & well-formed XSL stylesheet.
            xslTree = etree.parse(xslHandle)
            xslTransform = etree.XSLT(xslTree)

            self.stylesheetMap[(frameID, channelID)] = xslTransform
        except jinja2.TemplateError as err:
            pass #TODO: redirect to error page
        finally:
            if xslHandle is not None:
                xslHandle.close()

    
    def renderContent(self, xml, frameID, channelID = None):
                
        transform = self.stylesheetMap.get((frameID, channelID))
        
        if transform == None:
            return xml
        else:
            try:
                xmlHandle = StringIO(xml)
                documentTree = etree.parse(xmlHandle)
                result = transform(documentTree)                
                return str(result)
            finally:
                xmlHandle.close()



class Context:
    def __init__(self, appEnvironment):
        self.displayManager = appEnvironment.displayManager
        self.templateManager = appEnvironment.templateManager
        self.persistenceManager = appEnvironment.persistenceManager
        self.viewManager = appEnvironment.viewManager
        self.contentRegistry = appEnvironment.contentRegistry
        self.fileOutputPath = appEnvironment.outputPath
        self.urlBase = appEnvironment.urlBase
        self.frame = None
        self.method = None
        # experimental
        self.frontController = appEnvironment.frontController
   

class XMLTag:
    def __init__(self, allowedParamMap, xmlTemplate=None):
        self.allowedParams = allowedParamMap    # dictionary mapping param names to regular expressions
        self.template = xmlTemplate

    def respond(self, paramMap):
        pass

    def __call__(self, paramMap):
        return self.respond(paramMap)


class Responder:
    def __init__(self): pass

    def respond(self, httpRequest, context, **kwargs): pass
        
  
class Frame:
    def __init__(self):
        self.form = None

    def render(self, httpRequest, context, **kwargs): pass



class HTMLFrame(Frame):
    def __init__(self, htmlTemplate):
        self.template = htmlTemplate

    def render(self, httpRequest, context, **kwargs):
        return self.template.render(kwargs)


class StaticFrame(Frame):
    def __init__(self, contentFile):
        self.content = contentFile

        def render(self, httpRequest, context, **kwargs):
            pass


class XMLFrame(Frame):
    def __init__(self, xmlTemplate):
        self.template = xmlTemplate
        

    def render(self, httpRequest, context, **kwargs):
        xml = self.template.render(kwargs)
        channelID = httpRequest.params.get('channel')
        frameID = httpRequest.params.get('frame')
        
        return context.displayManager.renderContent(xml, frameID, channelID)


class MenuOption:
    def __init__(self, name, value):
        self.name = name
        self.value = value

    def __repr__(self):
        return 'MenuOption [name: %s, value: %s]\n' % (self.name, self.value)


class SQLDataSource:
    def __init(self):
        self.data = None

    def load(self, persistenceManager, **kwargs):
        pass

    def customQuery(self, dataTable, selectColumns, persistenceManager):
        return None

    def get_data(self):
        pass


class MenuDataSource(SQLDataSource):
    params = ['table', 'name_field', 'value_field']
    requiredParams = ['table']

    def __init__(self, tableName, nameField, valueField):
        self.tableName = tableName
        self.nameField = nameField
        self.valueField = valueField
        self.options = []

    def load(self, persistenceManager, **kwargs):
        dataTable = persistenceManager.loadTable(self.tableName)
        query = select([dataTable.columns[self.nameField], 
                        dataTable.columns[self.valueField]])
        
        for key in kwargs:
            query = query.where(dataTable.columns[key] == kwargs[key])

        resultSet = query.execute().fetchall()
        for row in resultSet:
            self.options.append(MenuOption(row[self.nameField], row[self.valueField]))
        
    def __call__(self):
        return self.options

    def get_data(self):
        return self.options


class LookupDataSource(SQLDataSource):
    params = ['table', 'key_field', 'value_field']
    requiredParams = ['table']

    def __init__(self, tableName, keyField, valueField):
        self.tableName = tableName
        self.keyField = keyField
        self.valueField = valueField
        self.data = {}

    def load(self, persistenceManager):
        dataTable = persistenceManager.loadTable(self.tableName)
        query = select([dataTable.columns[self.keyField], dataTable.columns[self.valueField]])
        resultSet = query.execute().fetchall()
        for row in resultSet:
            self.data[row[self.keyField]] = row[self.valueField]

    def __call__(self):
        return self.data

    def get_data(self):
        return self.data
        

class TableDataSource(SQLDataSource):
    params = ['table', 'fields', 'headers']
    requiredParams = ['table', 'fields']

    def __init__(self, tableName, columnNameArray, headerArray=None):
        self.tableName = tableName
        self.columnNameArray = columnNameArray
        
        if headerArray is None:
            self.header = columnNameArray
        else:
            self.header = headerArray

        self.data = []

    def load(self, persistenceManager, **kwargs):
        dataTable = persistenceManager.loadTable(self.tableName)
        selectColumns = []
        for name in self.columnNameArray:
            selectColumns.append(dataTable.columns[name])
        
        query =  self.customQuery(dataTable, selectColumns, persistenceManager)
        if query is None:
            query = select(selectColumns)

        for key in kwargs:
            query = query.where(dataTable.colums[key] == kwargs[key])

        resultSet = query.execute().fetchall()

        for row in resultSet:
            self.data.append(row)
            
    def __call__(self):
        return self.data
        
        
class ContentRegistry:
    def __init__(self): 
        self.frames = {}
        self.frameToFormMap = {}
        self.helperFunctions = {}
        
    def addFrame(self, frame, alias, formClass = None):
        self.frames[alias] = frame
        if formClass is not None:
            self.frameToFormMap[alias] = formClass

    def getFrame(self, frameID):
        if frameID not in self.frames:
            raise NoSuchFrameError(frameID)
        
        return self.frames[frameID]
    
    def hasForm(self, frameID):
        return frameID in self.frameToFormMap

    def getFormClass(self, frameID):
        if frameID not in self.frameToFormMap:
            raise NoSuchFormError(frameID)
        return self.frameToFormMap[frameID]

    def setHelperFunctionForFrame(self, frameID, helperFunction):
        if frameID not in self.frames:
            raise NoSuchFrameError(frameID)
        self.helperFunctions[frameID] = helperFunction

    def getHelperFunctionForFrame(self, frameID):
        if frameID not in self.helperFunctions:
            return None         # helper functions are optional
        return self.helperFunctions[frameID]


class ViewManager:
    def __init__(self, contentRegistry):
        self.contentRegistry = contentRegistry
        self.frameMap = {}

    def mapFrameID(self, frameID, objectType, controllerMethod):
        self.frameMap[(objectType, controllerMethod)] = frameID
        
    def getFrameID(self, objectType, controllerMethod):
        if (objectType, controllerMethod) not in self.frameMap:
            raise NoSuchViewError(objectType, controllerMethod)
        return self.frameMap[(objectType, controllerMethod)]


    
class SelectResponder(Responder):
    def __init__(self, dataSource):
        self.dataSource = dataSource
        self.templateFrameID = 'select_control'
        self.name = controlName

    def _respond(self, persistenceManager):
        
        self.dataSource.load(persistenceManager)
        return { 'options': self.dataSource(), 'control': self }

    def respond(self, httpRequest, context, **kwargs):
        pMgr = context.persistenceManager
        
        dict = self._respond(pMgr)
        frameObject = context.contentRegistry.getFrame(self.templateFrameID)
        return frameObject.render(httpRequest, context, **dict)
        

class RadioGroupResponder(Responder):
    def __init__(self, dataSource):
        self.dataSource = dataSource
        self.templateFrameID = 'radio_control'
        self.name = controlName

    def _respond(self, persistenceManager):
        
        self.dataSource.load(persistenceManager)
        return { 'options': self.dataSource(), 'control': self }

    def respond(self, httpRequest, context, **kwargs):
        pMgr = context.persistenceManager
        
        dict = self._respond(pMgr)
        frameObject = context.contentRegistry.getFrame(self.templateFrameID)
        return frameObject.render(httpRequest, context, **dict)







class DataSourceFactoryPlugin:
    def __init__(self):
        pass

    def getRequiredParams(self): # implement in subclass; return an array of param names
        pass

    def createDataSource(self, **kwargs): # implement in subclass
        pass

    requiredParams = property(getRequiredParams)



class DataSourceFactory:
    def __init__(self):
        self.dataSourceCreators = {'menu': '_createMenuSource', 
                                   'grid': '_createTableSource' }
        self.dataSourcePlugins = {}


    def registerPlugin(self, dataSourceFactoryPlugin, dataSourceType):
        self.dataSourcePlugins[dataSourceType] = dataSourceFactoryPlugin


    def createDataSource(self, dataSourceType, **kwargs):
        
        if dataSourceType in self.dataSourceCreators:
            print 'Processing datasource type... %s' % dataSourceType
            return getattr(self, self.dataSourceCreators[dataSourceType])(**kwargs)
        else:
            try:
                plugin = self.dataSourcePlugins[dataSourceType]
                missingParams = [arg for arg in plugin.requiredParams if arg not in kwargs]
                if missingParams:
                    raise Exception("Missing init param in call to DataSourceFactory plugin.")
                return plugin.createDataSource(**kwargs)
            except KeyError, err:
                raise NoSuchDataSourcePluginError(dataSourceType)
            

    def _createMenuSource(self, **kwargs):

        requiredParams = ['table']
        missingParams = [arg for arg in requiredParams if arg not in kwargs]
        if missingParams:
            raise MissingDataSourceParameterError(MenuDataSource, 
                                                  requiredParams)

        table = kwargs['table']
        nameField = kwargs.get('name_field', 'name')  # default values
        valueField = kwargs.get('value_field', 'id')
        source = MenuDataSource(table, nameField, valueField)
        return source



    def _createTableSource(self, **kwargs):
        requiredParams = ['table', 'fields']

        print "Received TableSource params: %s " % kwargs
        try:
            table = kwargs['table']
            fieldListString = kwargs['fields']
            fields = [item.strip() for item in fieldListString.split(',')]

            headers = None
            headerListString = kwargs.get('headers', None)
            if headerListString:
                headers = [item.strip() for item in headerListString.split(',')]
            
            #conditions = kwargs.get('conditions', None)  # optional, not implemented yet 
            
            source = TableDataSource(table, fields, headers)
            return source
        except KeyError, err:
            raise MissingDataSourceParameterError(MenuDataSource, 
                                                  requiredParams)
            
            
            

                
        
        
        



        

            
        
        
