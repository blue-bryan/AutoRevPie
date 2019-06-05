
import os
import sys
import time
import datetime
import configparser

from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.common.exceptions import TimeoutException

import AutomateRevPie.AutomateRevPie as AutoRP
import AutomateRevPie.config as Config

def openLog():
    ''' Will open (or create a file if none exists),
        named 'logs.txt' in the working directory. '''

    # open log file and print header to file
    with open(Config.logs_path, 'w') as f:
        print('Filename:', Config.logs_path, file=f)
        print('\n - - - Logs (' + str(time.strftime("%Y-%m-%d %H:%M.%S")) + ')' + ' - - - ' + '\n\n', file=f)

###############################################################################
# Program start...

print("\n####################################################################\n")
print("\nloading . . . \n")

# Open log file 'log.txt' for logging
try:
    openLog()
except KeyboardInterrupt:
    sys.exit(1)
except Exception as err:
    AutoRP.printToLog("\n\nopenLog: Error while loading '/log.txt', logs will not be recorded\n"
                , err, Config.logs_path)
    sys.exit(1)

################################ CONFIG #######################################
# CONFIG FILE SHOULD BE IN THE WORKING DIRECTORY

# get config file
try:
    # open file
    configParser = configparser.RawConfigParser()
    configParser.read_file(open(os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
                            + "/config.txt"))
    # save to variables
    admin = r"{}".format(configParser.get('website-urls', 'admin'))
    wallboard = r"{}".format(configParser.get('website-urls', 'wallboard'))
    queueDetails = r"{}".format(configParser.get('website-urls', 'queueDetails'))
    queue_uname = r"{}".format(configParser.get('login-info', 'username'))
    queue_pass = r"{}".format(configParser.get('login-info', 'password'))
except KeyboardInterrupt:
    print("\n")
    sys.exit(1)
except Exception as err:
    AutoRP.printToLog("\n\nconfigParser: Error while reading config file 'config.txt', closing..."
                , err, Config.logs_path)
    sys.exit(1)

############################# browser setup ###################################

AutoRP_obj = AutoRP.AutoRevPie(admin, 0, 1)
BidAdjuster = AutoRP_obj.autoBidAdjust()
try:
    # load admin page
    AutoRP.browser.execute_script("window.open('" + admin + "')")
    # login to admin
    AutoRP.waiting(1)
    AutoRP.switchToTab(AutoRP_obj.bidsPageTab)
    login = True
    while login:
        try:
            login = AutoRP.checkBrowser()
            AutoRP.admin_login(AutoRP.getLoginInfo("-u"), AutoRP.getLoginInfo("-p"))
        except KeyboardInterrupt:
            print("\n")
            sys.exit(1)
        except Exception as err:
            AutoRP.printToLog("\nError: Incorrect Username/Password, try again\n"
                        , err, Config.logs_path)
            print("\n . . . \n")
        else:
            login = False
    # load page for bid adjustments
    AutoRP_obj.openBidAdjustments()
    AutoRP.browser.execute_script("revPieBidAdjustments('390', 'RP101_8am_to_11am')")

    AutoRP.waiting(3)
    AutoRP.browser.execute_script("changeBidAdjustmentsDateFilter('all')")
    AutoRP.waiting(10)
    check = True
    while check:
        if (str(AutoRP.browser.find_element_by_id(
                'bidAdjustmentsDateFilter').get_attribute(
                        "value")) == "all"):
            check = False
        else:
            AutoRP.checkBrowser()
    Bids = BidAdjuster.copyBids()
    sourceIDs = Bids[0]
    WebDriverWait(AutoRP.browser, 15).until(
            expected_conditions.presence_of_element_located(
                    (By.ID, 'bidAdjustmentsTable')))
    for index, item in enumerate(sourceIDs):
        _customBidID = r"customBid_" + str(item)
        print(_customBidID)
        AutoRP.waiting(1)
        try:
            text_area = AutoRP.browser.find_element_by_id(_customBidID)
        except:pass
        else:
            if Bids[2][index] != "0.01" and item != "1332" and item !="1250" and item != "1252" and item != "580" and item != "518" and item != "536" and item != "383":
                text_area.send_keys(Keys.CONTROL, 'a')
                AutoRP.waiting(1)
                text_area.send_keys("0.01")
                AutoRP.waiting(1)
                AutoRP.browser.execute_script("makeCustomBidAdjustment('" + str(item) + "')")
except KeyboardInterrupt:
    print("\n")
    sys.exit(1)
except Exception as err:
    AutoRP.printToLog("\n\nError while loading tabs, closing...\n"
                , err, Config.logs_path)
    AutoRP.browser.quit()
    sys.exit(1)


