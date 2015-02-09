
from environment import *


e = Environment()
e.bootstrap('ilook.conf')
specs = e.exportDatasourceSpecs()

print specs
