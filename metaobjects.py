
from wtforms import *


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

class SelectFieldSpec(FieldSpec):

    def __init__(self, name, label, menuDict):
        FieldSpec.__init__(name, label, SelectField)
        
        menuChoices = []
        for key in menuDict:
            menuChoices.append("('%s', '%s')" % key, menuDict[key])

        self.extraData.append("choices = [%s]" % ",".join(menuChoices))

class FormSpec:
    """A specification for a WTForms form instance.

      A FormSpec instance provides the basis for generating boilerplate code, templates, and Form instances 
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
                         "TINYINT": BooleanField, 
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
        
        

