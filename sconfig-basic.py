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



class SkeletonAppConfig:

    def __init__(self):
        self.projectName = None
        self.web_app_name = None
        self.app_root = None
        self.static_file_path = None
        self.stylesheet_path = None
        self.template_path = None
        self.default_forms_package = None
        self.default_model_package = None
        self.default_controller_package = None
        self.default_helper_package = None
        self.default_datasource_package = None
        
        self.app_version = '1.0'
        
        
    def getProjectName(self, screen):
        screen.clear()
        Notice('Welcome to Serpentine. This utility will help you generate a simple default config.').show(screen)
        prompt = TextPrompt('Please choose a project name:', None)
        return prompt.show(screen)
        
        
    def getWSGIParams(self, screen):
        """Get the settings for the app's interface with Apache

        Arguments:
        screen -- display target for menus and prompts
        """
        screen.clear()
        Notice('Enter WSGI config information.').show(screen)
        hostPrompt = TextPrompt('Enter the hostname for this app: ', 'localhost')
        hostname = hostPrompt.show(screen)
        
        portPrompt = TextPrompt('Enter HTTP port for this app: ', '9000')
        port = portPrompt.show(screen)
       
        return { 'hostname': hostname, 'port': port }
                
        
    def run(self, screen):
        currentDir = os.getcwd()
        bootstrapDir = os.path.join(currentDir, "bootstrap")
        env = jinja2.Environment(loader = jinja2.FileSystemLoader(bootstrapDir))
        templateMgr = JinjaTemplateManager(env)

        # now generate the config file

        configFile = None
        wsgiFile = None
        wsgiVHostEntryFile = None
        baseTemplateFile = None
        try:
            self.projectName = self.getProjectName(screen)
                        
            self.app_name = self.projectName
            
            self.web_app_name = self.projectName.lower()
            self.url_base = self.projectName.lower()
            
            wsgiParams = self.getWSGIParams(screen)
            self.hostname = wsgiParams['hostname']
            self.port = wsgiParams['port']

            
            self.app_root = os.getcwd()
            # this is a standalone global in the config, so it must be an absolute path
            self.static_file_path = os.path.join(self.app_root, "templates") 
            
            self.stylesheet_path = 'stylesheets'
            self.template_path = 'templates'

            self.default_form_package = '%s_forms.py' % self.web_app_name
            self.default_model_package = '%s_models.py' % self.web_app_name
            self.default_controller_package = '%s_controllers.py' % self.web_app_name
            self.default_responder_package = '%s_responders.py' % self.web_app_name
            self.default_helper_package = '%s_helpers.py' % self.web_app_name
            self.default_datasource_package = '%s_datasources.py' % self.web_app_name
            self.default_report_package = '%s_reporting.py' % self.web_app_name
            self.startup_db = 'None'

            self.models = []
            self.controllers = []
            self.xmlFrames = []            
            self.databases = []
        
            configFileTemplate = templateMgr.getTemplate('config_template.tpl')
            configFilename = '%s.conf' % self.projectName.lower()
            configFile = open(os.path.join('bootstrap', configFilename), 'w')
            configFile.write(configFileTemplate.render(config = self))
            
            wsgiFile = open(os.path.join('bootstrap', '%s.wsgi' % self.web_app_name), 'w')
            wsgiFileTemplate = templateMgr.getTemplate("wsgi_file.tpl")
            wsgiData = wsgiFileTemplate.render(config = self)
            wsgiFile.write(wsgiData)
            
            wsgiVHostEntryFile = open(os.path.join('bootstrap', '%s_vhost_entry.xml' % self.web_app_name), 'w')
            wsgiVHostTemplate = templateMgr.getTemplate('wsgi_vhost_entry.tpl')
            wsgiVHostData = wsgiVHostTemplate.render(config = self)
            wsgiVHostEntryFile.write(wsgiVHostData)
            
            baseTemplate = templateMgr.getTemplate('base_html_template.tpl')
            baseTemplateData = baseTemplate.render(config = self)
            baseTemplateFilename = os.path.join('bootstrap', 'base_template.html')
            baseTemplateFile = open(baseTemplateFilename, 'w')
            baseTemplateFile.write(baseTemplateData)

        finally:
            if configFile:
                configFile.close()

            if wsgiFile:
              wsgiFile.close()
            
            if wsgiVHostEntryFile:
              wsgiVHostEntryFile.close()

            if baseTemplateFile:
                baseTemplateFile.close()
def main():
    display = CursesDisplay(SkeletonAppConfig)
    display.open()
    
    
    
if __name__ == '__main__':
    main()
