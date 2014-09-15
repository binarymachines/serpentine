#------ Reporting module ---------


from db import *
from xlwt import *
from bottle import *

import os



class NoSuchReportException(Exception):
      def __init__(self, reportName):
            Exception.__init__(self, 
                               'No report registered with the name %s.' % reportName)


class ReportField(object):
    def __init__(self, attributeName, attributeLabel, callParameter = None, **kwargs):
        self.attributeName = attributeName
        if attributeLabel is None:
            self.label = self.attributeName
        else:
            self.label = attributeLabel
        
        self.callParameter = callParameter
        self.defaultValue = kwargs.get('default', None)
        self.value = None

    def populate(self, targetObject, **kwargs):
        if self.defaultValue is not None:
            self.value = self.defaultValue
            return self.value

        attr = getattr(targetObject, self.attributeName)
        if hasattr(attr, '__call__'):
            if self.callParameter:
                # distinguish explicit params from references
                if str(self.callParameter)[0:1] == '$':
                    # reference
                    realParam = kwargs[self.callParameter[1:]]                    
                    self.value = attr(realParam)
                else:
                    # explicit param value
                    self.value = attr(self.callParameter)
            else:
                self.value = attr()
        else:
            self.value = attr
        
        return self.value


class ReportDataSource:
    def __init__(self, reportFieldArray=[]):
        self.fields = reportFieldArray
        self.data = None

    def addFields(self, reportFieldArray):
        self.fields.extend(reportFieldArray)
          
    def _getData(self, persistenceManager, **kwargs):
        """Load the report data from the DB via the persistence manager
        and a variable parameter set in kwargs. Override this method 
        in subclasses to retrieve report data.

        """
        return []

    def load(self, persistenceManager, **kwargs):
        self.data = self._getData(persistenceManager, **kwargs)


class ReportGenerator:
      def __init__(self, mimeType, fileExtension='rpt'):
            self.mimeType = mimeType
            self.fileExtension = fileExtension

      def generate(self, reportDataSource, reportTitle):
            pass


class ExcelReportGenerator(ReportGenerator):
      def __init__(self):
      	  ReportGenerator.__init__(self, 'application/vnd.ms-excel', 'xls')

      def generate(self, reportDataSource, reportTitle):

            #create spreadsheet
            workbook = Workbook()
            docSheet1 = workbook.add_sheet(reportTitle[0:31]) # upper limit on spreadsheet name length

            headerFontStyle = XFStyle()
            bodyFontStyle = XFStyle()

            headerFont = Font()
            headerFont.name = 'Arial'
            headerFont.bold = True

            bodyFont = Font()
            bodyFont.name = 'Times New Roman'
    

            headerFontStyle.font = headerFont
            bodyFontStyle.font = bodyFont

            # write report header
            header = []
            colNumber = 0
            for field in reportDataSource.fields:                                  
                  header.append(field.label)
                  docSheet1.write(0, colNumber, field.label, headerFontStyle)
                  colNumber = colNumber + 1


            # now write the body 
            
            for rowNumber in range (1, len(reportDataSource.data)):
                  colNumber = 0
                  record = reportDataSource.data[rowNumber - 1]
                  for field in reportDataSource.fields:
                      
                      #print 'Field: %s  Value: %s' % (field.label, str(value))
                      dataValue = str(record[colNumber])
                      docSheet1.col(colNumber).width = max(len(dataValue) * 512, len(header[colNumber]) * 256)
                      docSheet1.write(rowNumber, colNumber, dataValue, bodyFontStyle)
                      colNumber = colNumber + 1
                  
            return workbook



class Report:
      def __init__(self, dataSource, reportGenerator, form):
            self.dataSource = dataSource      
            self.reportGenerator = reportGenerator
            self.form = form
            
      def getFileExtension(self):
            return self.reportGenerator.fileExtension

      def getMIMEType(self):
            return self.reportGenerator.mimeType

      def run(self, reportTitle, persistenceManager, reportGenerator=None, **kwargs):
            if reportGenerator is None:
                  generator = self.reportGenerator
            else:
                  generator = reportGenerator

            self.dataSource.load(persistenceManager, **kwargs)
            return generator.generate(self.dataSource, reportTitle)

      mimeType = property(getMIMEType)
      fileExtension = property(getFileExtension)
         

class ReportManager:
    def __init__(self, fileOutputPath):
        self.fileOutputPath = fileOutputPath
        self.reportMap = {}

    def registerReport(self, reportID, report):
          self.reportMap[reportID] = report

    def _runReport(self, report, reportTitle, persistenceManager, **kwargs):
          return report.run(reportTitle, persistenceManager, **kwargs)

    def runReport(self, reportID, httpRequest, context, **kwargs):
          report = self.reportMap.get(reportID, None)
          if report is None:
                raise NoSuchReportException(reportID)

          reportTitle = httpRequest.GET.get('report_title', '')
          inputForm = report.form
          inputForm.process(httpRequest.GET)
          if not inputForm.validate():
                raise FormValidationError('ReportManager', reportID, inputForm.errors)
     
          if not reportTitle:
                httpRequest.GET['report_title'] = 'untitled_report'

          kwargs.update(inputForm.data)          
          document = self._runReport(report, reportTitle, context.persistenceManager, **kwargs)

          reportFilename = '%s.%s' % (reportTitle, report.fileExtension)
          filename = os.path.join(self.fileOutputPath,  reportFilename)
          document.save(filename)

          return static_file(reportFilename, root=self.fileOutputPath, mimetype=report.mimeType, download=True)
