import os
import time
import datetime

# Will get a given file directory path
def getfpath(_filename): return(os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(_filename))))

config_path = (os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__))))
