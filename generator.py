from __future__ import print_function
from __future__ import unicode_literals

import os
import sys
import cgi
from io import StringIO

from lxml import etree


class FeedComponent:
    def __init__(self):
        pass

    def isValid(self):
        return False


class Enclosure(FeedComponent):
    def __init__(self, url, length, mimeType):
        self.url = url
        self.length = length
        self.mimeType = mimeType

    def isValid(self):
        if self.url is None:
            return False
        if self.length is None:
            return False
        if self.mimeType is None:
            return False

        return True

    def toXML(self):
        element = etree.Element('enclosure')
        element.set('url', self.url)
        element.set('length', self.length)
        element.set('type', self.mimeType)

        return element


class Category(FeedComponent):
    def __init__(self, name, domain=None):
        self.name = name
        self.domain = domain

    def isValid(self):
        if self.name is None:
            return False
        else:
            return True

    def toXML(self):
        element = etree.Element('category')
        element.text = self.name
        if self.domain is not None:
            element.set('domain', self.domain)

        return element

        


class Item(FeedComponent):
    def __init__(self, title, link, description):
        self.data = {}
        self.categories = []
        self.enclosure = None

        self.data['title'] = title
        self.data['link'] = link
        self.data['description'] = description
        
        # TODO: store regex in this table to validate data format
        self.optionalElements = {'link': None,                              
                                 'author': None,
                                 'comments': None,                              
                                 'guid': None,
                                 'pubDate': None,
                                 'source': None }


    def setData(self, name, value):        
        self.data['name'] = value
        # TODO: validate against regex

    def setEnclosure(self, dict):
        self.enclosure = Enclosure(dict)

    def addCategory(self, value, domain=None):
        self.categories.append({ 'name': value, 'domain': domain})


    def toXML(self):
        itemElement = etree.Element('item')

        for key in self.data:
            itemSubElement = etree.SubElement(itemElement, key)
            itemSubElement.text = self.data[key]
        
        if self.enclosure is not None:
            itemElement.append(self.enclosure.toXML())

        for category in self.categories:
            itemElement.append(category.toXML())

        return itemElement
        

    def isValid(self):
        return false
        

class Channel(FeedComponent):
    def __init__(self, title, link, description):
        # TODO: check formats against regexes
        self.data = { 'title': title, 'link': link, 'description': description }
        self.items = []
        
        # subject to change depending on the format we decide on
        self.optionalElements = ['language', 
                                 'pubDate', 
                                 'lastBuildDate', 
                                 'docs', 
                                 'generator',
                                 'managingEditor',
                                 'webMaster']


    def setElementData(self, elementName, value):
        self.data['name'] = value

    def addItem(self, itemObject):
        self.items.append(itemObject)

    def toXML(self):
        channelElement = etree.Element('channel')
        titleElement = etree.SubElement(channelElement, 'title')
        titleElement.text = self.data.get('title', '')

        linkElement = etree.SubElement(channelElement, 'link')
        linkElement.text = self.data.get('link', '')

        descriptionElement = etree.SubElement(channelElement, 'description')
        descriptionElement.text = self.data.get('description', '')

        for item in self.items:
            channelElement.append(item.toXML())

        return channelElement


    def isValid(self):
        if self.data.get('title') is None:
            return False
        if self.data.get('link') is None:
            return False
        if self.data.get('description') is None:
            return False

        return True

    
    
class RSSFeed(FeedComponent):
    def __init__(self, channelArray):
        self.version = '2.0'
        self.channels = channelArray

    def addChannel(self, channel):
        self.channels.append(channel)

    def toXML(self):
        docRoot = etree.Element('rss')
        docRoot.set('version', self.version)
        for channel in self.channels:             
            docRoot.append(channel.toXML())

        return docRoot
            

if __name__ == "__main__":		
	
       myChannel = Channel('foobar', 'http://foobar.healthination.com', 'Latest foo news from Healthi')
       newItem = Item('Smoking Is Bad For You', 
                       'http://www.healthination.com/smokingisbad', 
                       'Your Zodiac sign: lung Cancer.')
       newItem2 = Item('Eat More Kale',
                'http://www.healthination.com/morekale',
                'Your health forecast: Kale-Force Winds')

       myChannel.addItem(newItem)
       myChannel.addItem(newItem2)
       myFeed = RSSFeed([myChannel])

       xmlDoc = myFeed.toXML()
       str = etree.tostring(xmlDoc, pretty_print = True)
       







