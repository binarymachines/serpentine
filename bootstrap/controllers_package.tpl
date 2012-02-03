#!/usr/bin/python

from core import BaseController

{% for controller in config.controllers %}

class {{ config.controllers[controller].name }}(BaseController):
    def __init__(self, modelClass):
        BaseController.__init__(self, modelClass)


{% endfor %}

