#------ Reporting module ---------


from bottle import redirect, static_file
from db import *
from sqlalchemy import update
from xlwt import *

import os


class ExcelReportGenerator():
      def __init__(self):
      	  pass

      def createSpreadsheet(self, sqlaResultProxy, fieldMap, reportName = 'wsreport'):

            results = sqlaResultProxy.fetchall()            
            cols = sqlaResultProxy._metadata.keys
            
            #create spreadsheet
            workbook = Workbook()
            docSheet1 = workbook.add_sheet(reportName)

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
            for column in cols :        
                  if column in fieldMap:
                        colName = fieldMap[column]
                  else:
                        colName = column
        
                  header.append(colName)
                  docSheet1.write(0, colNumber, colName, headerFontStyle)
                  colNumber = colNumber + 1


            # now write the body 

            rowNumber = 1
            for record in results:
                  colNumber = 0
                  for column in cols :
                        data = getattr(record, column)
                        docSheet1.col(colNumber).width = max(len(str(data)) * 512, len(header[colNumber]) * 256)
                        docSheet1.write(rowNumber, colNumber, str(data), bodyFontStyle)
                        colNumber = colNumber + 1
                  rowNumber = rowNumber +1
 
            return workbook
   
         
class ReportManager:
    def __init__(self, fileOutputPath):
        self.rgen = ExcelReportGenerator()
        self.fileOutputPath = fileOutputPath

    def contact_logs_by_date(self, httpRequest, context, **kwargs):
        
        startDate = kwargs['start_date']
        endDate = kwargs['end_date']
        

        cLogs = context.persistenceManager.getTableForType('businessTypes.ContactLog')
        statement = cLogs.select(and_(cLogs.c.contact_date >= startDate, cLogs.c.contact_date <= endDate))

        fieldMap = {}
        workbook = self.rgen.createSpreadsheet(statement.execute(), fieldMap)

        reportFilename = 'report' + sys._getframe().f_code.co_name + '.xls'
        filename = os.path.join(self.fileOutputPath,  reportFilename)
        workbook.save(filename)

        return static_file(reportFilename, root=self.fileOutputPath, mimetype='application/vnd.ms-excel')

    
    def contacts_by_zip(self, httpRequest, context, **kwargs):
          
          zipcode = kwargs['zip']

          persons = context.persistenceManager.getTableForType('businessTypes.Person')
          statement = persons.select(persons.c.zip == zipcode)

          fieldMap = {}
          workbook = self.rgen.createSpreadsheet(statement.execute(), fieldMap)

          reportFilename = 'report' + sys._getframe().f_code.co_name + '.xls'
          filename = os.path.join(self.fileOutputPath,  reportFilename)
          workbook.save(filename)

          return static_file(reportFilename, root=self.fileOutputPath, mimetype='application/vnd.ms-excel')
