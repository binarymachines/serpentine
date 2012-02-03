
from db import *

class SamplePlugin(PersistenceManagerPlugin):
    def __init__(self):
        pass

    def execute(self, pMgr, object):
        return "Hello, pluggable world!"
