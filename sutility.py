import logging

class Enum(set):
    def __getattr__(self, name):
        if name in self:
            return name
        raise AttributeError


logger = logging.getLogger("serpentine")
logger.setLevel(logging.INFO)
 
# create the logging file handler
fh = logging.FileHandler("serpentine.log")
 
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
 
# add handler to logger object
logger.addHandler(fh)
