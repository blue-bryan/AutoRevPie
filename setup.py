import AutomateRevPie.config as Config

# Generate logs file path
_fpath = Config.getfpath(__file__)
with open((Config.config_path + "/config.ini"), 'w') as f:
    print(_fpath + "/logs.txt", file=f)
