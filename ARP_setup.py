import AutomateRevPie as AutomateRP

# Generate config file with logs file path
_fpath = AutomateRP.Config.getfpath(__file__)
with open((AutomateRP.Config.config_path + "/config.ini"), 'w') as f: print(_fpath, end="", file=f)
