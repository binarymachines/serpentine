from wtforms import *
#from plugin import *


class NoSuchFieldConfigError(Exception):
    def __init__(self, name):
        Exception.__init__(self, "No FieldConfig named %s in this FormConfig." % name)


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

    def __repr__(self):
        return 'Controller: %s | Alias: %s | Model: %s | Methods: %s' % (self.name, self.alias, self.model, self.methods)

class WSGIConfig:
    def __init__(self, hostName, portNumber):
        self.host = hostName
        self.port = int(portNumber)


class DatabaseConfig:
    def __init__(self, host, schema, username, password):
        self.type = "mysql"
        self.host = host
        self.schema = schema
        self.username = username
        self.password = password

    def __repr__(self):
        return 'connected to %s DB instance on host "%s" as user %s, schema: %s' % (self.type, self.host, self.username, self.schema)


class PluginSlotConfig:
    def __init__(self, methodName, urlRoute, requestType):
        self.method = methodName
        self.variables = []
        
        self.routeExtensionObject = RouteExtension(urlRoute)
        self.route_extension_string = str(self.routeExtensionObject)
        for element in self.routeExtensionObject:
            if not element.isStatic():
                self.variables.append(element.elementString)
        self.request_type = requestType
        self.plugin_alias = None
        

    def generateRoutingFunctionName(self):
        pluginString = self.plugin_alias  # [0].upper() + self.plugin_alias[1:]
        methodString = self.method[0].upper() + self.method[1:]
        requestTypeString = self.request_type.lower().capitalize()
        return 'plugin_%sMethod%s%s' % (pluginString, methodString, requestTypeString)

    def generateFunctionSignature(self):
        return 'environment, %s' % (', '.join("%s = 'none'" % variable for variable in self.variables))


    #def getPluginMethodArgs(self):
    #    for var in variables

    functionName = property(generateRoutingFunctionName)
    functionSignature = property(generateFunctionSignature)
    #pluginMethodArgs = property(getPluginMethodArgs)
    

class PluginConfig:
    def __init__(self, pluginClassname, pluginAlias, moduleName = 'user_plugins'):
        self.classname = pluginClassname
        self.alias = pluginAlias
        self.modulename = lower(moduleName)
        self._slots = {}


    def addSlot(self, pluginSlotConfig):
        pluginSlotConfig.plugin_alias = self.alias
        self._slots[pluginSlotConfig.method] = pluginSlotConfig
                          

    def getSlots(self):
        return self._slots.values()


    def getSlot(self, methodName):
        return self._slots.get(methodName)


    def listSlots(self):
        return self._slots.keys()
        
    slots = property(getSlots)



class FrameConfig:
    def __init__(self, name, template, formClassName, frameType, helperName = None):
        self.name = name
        self.template = template
        self.form = formClassName
        self.type = frameType
        self.helper = helperName


class ModelConfig(object):
    def __init__(self, name, table, children = None):
        self.name = name
        self.table = table
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



class DataSourceParameter:
    def __init__(self, name, value):
        self.name = name
        self.value = value


class DataSourceConfig:
    def __init__(self, dataSourceType, parameterArray):
        self.type = dataSourceType
        self.params = parameterArray

    def __repr__(self):
        result = ''
        for p in self.params:
            result += '%s: %s, ' % (p.name, p.value)

        return result[:-2]

    
class FieldConfig:
    """A specification for a field in a WTForms form instance."""

    def __init__(self, name, label, type, required = False, hidden = False):
        self.name = name
        self.label = label
        self.type = type
        self.required = required
        self.hidden = hidden
        self.extraData = []

        # displayClass is the CSS class designator for the field.
        # we default to the standard for the Foundation CSS kit.

        self.displayClass = 'input-text'

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


class SelectFieldConfig(FieldConfig):

    def __init__(self, name, label, menuDict):
        FieldSpec.__init__(name, label, SelectField)
        
        menuChoices = []
        for key in menuDict:
            menuChoices.append("('%s', '%s')" % key, menuDict[key])

        self.extraData.append("choices = [%s]" % ",".join(menuChoices))


class FormConfig:
    """A specification for a WTForms form instance.

      A FormConfig instance provides the basis for generating boilerplate code, templates, and Form instances 
      in Serpentine.
      """

    def __init__(self, model, urlBase):
        self.model = model
        self.urlBase = urlBase
        self.formClassName = "%sForm" % self.model
        self.fields = []

    def __repr__(self):
        return self.formClassName

    def addField(self, fieldConfig):
        """Add the passed FieldConfig instance to this FormConfig."""

        self.fields.append(fieldConfig)

    def getField(self, name):
        """Retrieve a FieldConfig by name."""

        for field in self.fields:
            if field.name == name:
                return field

        raise NoSuchFieldConfigError(name)


class FieldConfigFactory:
    """Use Factory pattern to create a FieldConfig from reflected information about a database column."""

    def __init__(self):
        self.typeMap = { "BOOL": BooleanField, 
                         "INTEGER": IntegerField, 
                         "FLOAT": DecimalField, 
                         "DOUBLE": DecimalField, 
                         "DATE": DateField, 
                         "DATETIME": DateTimeField,
                         "INTEGER": IntegerField, 
                         "TINYINT": BooleanField, 
                         "VARCHAR": TextField }

        self.selectFields = {}
    
    def specifySelectField(self, name, dictionary):
        self.selectFields[name] = dictionary
        
    def create(self, tableColumn):
        """Create a field configuration object based on the information in the column object.

        Arguments:
        --tableColumn: an SQLAlchemy reflected Column object 

        Returns:
        -- a valid FieldConfig instance
        """

        fieldName = tableColumn.name
        fieldLabel = self.convertColumnNameToLabel(tableColumn.name)

        if fieldName == "id":
            fieldType = HiddenField
            required = False
        elif fieldName in self.selectFields:
            return SelectFieldConfig(fieldName, fieldLabel, self.selectFields[fieldName])
        else:
            fieldType = self.determineFieldType(str(tableColumn.type))
            required = not tableColumn.nullable

        # TODO: Add some logic for finding out about hidden fields
        return FieldConfig(fieldName, fieldLabel, fieldType, required, False)
           

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
           

class ControlConfig:
    """A configuration for a Serpentine dynamic UI control.

    A ControlConfig is rendered directly into YAML by the SConfigurator.
    """

    def __init__(self, type, name, dataSourceAlias, templateID = None):
        self.type = type
        self.name = name
        self.datasource = dataSourceAlias
        self.template = templateID
        


class ObjectParameter:
    def __init__(self, name, value):
        self.name = name
        self.value = value
        

class ControlPackage:
    """ A template populator for a generated Javascript code segment.
    """
    
    
    def __init__(self, name, div_name='div_id', params = [], callback='null'):
        self.name = name
        self.parameterList = params
        self.div_name = div_name
        self.callback = callback
        
    
    def getParams(self):
        if not self.parameterList:
            return 'null'
        
        paramStrings = ['%s: "%s"' % (p.name, p.value) for p in self.parameterList]
        result = "{ %s }" % (', '.join(paramStrings))
        return result
        
        
    params = property(getParams)


class URLPackage:
    def __init__(self):
        self.object_type = None
        self.object_name = None
        self.parameterList = []
    
    def getQueryString(self):
        paramStrings = ['%s=%s' % (p.name, p.value) for p in self.parameterList]
        result = '?%s' % ('&'.join(paramStrings))
        return result
        
    query_string = property(getQueryString)
    
    
    
class FrameRequestURLPackage(URLPackage):
    def __init__(self, frameID):
        self.object_name = frameID
        self.object_type = 'frame'
        

class ControllerURLPackage(URLPackage):
    """A template populator for a generated Controller URL."""
    
    def __init__(self, controllerID, methodName, objectParameters = []):        
        self.object_name = controllerID
        self.object_type = 'controller'
        self.parameterList = objectParameters
        
    
class ResponderURLPackage(URLPackage):
    """A template populator for a generated Responder URL."""
    
    def __init__(self, responderID, objectParameters = []):
        self.object_name = responderID
        self.object_type = 'responder'
        self.parameterList = objectParameters
        
    



