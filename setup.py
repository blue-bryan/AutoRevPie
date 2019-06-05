import os
import AutomateRevPie.config as Config

# Generate logs file path
_fpath = Config.getfpath()
with open((_fpath + "/config.ini"), 'w') as f:
    print(os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__))) + "/logs.txt", file=f)
