import os

# Will get a given file directory path
def getfpath(_filename): return(os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(_filename))))

config_path = (os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__))))

# open and read auto generated config.ini to get logs file path
with open ((config_path+"/config.ini"), 'r') as f: logs_path=f.readline()
