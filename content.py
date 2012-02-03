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
logging.basicConfig( filename = 'wellspring.log', level = logging.INFO, format = "%(asctime)s - %(message)s" )

log = logging.info



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


    
        
    
