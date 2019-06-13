import AutomateRevPie.config as Config

# Read config file to get logs file path
_fpath = Config.getfpath(__file__)
with open((Config.config_path + "/config.ini"), 'w') as f: print(_fpath, end="", file=f)
