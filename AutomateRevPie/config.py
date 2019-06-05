import os

# get working directory path
def getfpath(): return(os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__))))

# open and read auto generated config.ini to get logs file path
with open ((getfpath()+"/config.ini"), 'r') as f: logs_path=f.readline()
