import AutomateRevPie as AutomateRP

# Generate config file with logs file path
_fpath = AutomateRP.ARP_WebDriver.Config.getfpath(__file__)
with open((AutomateRP.ARP_WebDriver.Config.config_path + "/config.ini"), 'w') as f: print(_fpath, end="", file=f)
