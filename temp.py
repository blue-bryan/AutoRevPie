
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

import AutomateRevPie.AutomateRevPie as ARP
import AutomateRevPie.config as Config

###############################################################################
# Program start...

with open(Config.getfpath(__file__)+"/AutoRevPie.info", 'r') as f:
    print(" . . . ", f.readline())
print("\nloading . . . \n")

# Open log file 'logs.txt' for logging
try:
    with open(ARP.ErrorHandler().getLogFile(), 'w') as f:
        print('Filename:', ARP.ErrorHandler().getLogFile(), file=f)
        print('\n - - - Logs (' + str(time.strftime("%Y-%m-%d %H:%M.%S")) + ')' + ' - - - ' + '\n\n', file=f)
        _loop = False
except KeyboardInterrupt:
    sys.exit(1)
except Exception:pass

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
    ARP.ErrorHandler().printToLog("\n\nconfigParser: Error while reading config file 'config.txt', closing..."
                , err, ARP.ErrorHandler().getLogFile())
    sys.exit(1)

############################# browser setup ###################################

AutoRP_obj = ARP.AutoRevPie(admin, 0, 1)
BidAdjuster = AutoRP_obj.autoBidAdjust()
try:
    # load admin page
    ARP.browser.execute_script("window.open('" + admin + "')")
    # login to admin
    ARP.ErrorHandler().waiting(1)
    ARP.ErrorHandler().switchToTab(AutoRP_obj.bidsPageTab)
    login = True
    while login:
        try:
            login = ARP.ErrorHandler().checkBrowser()
            ARP.admin_login(ARP.getLoginInfo("-u"), ARP.getLoginInfo("-p"))
        except KeyboardInterrupt:
            print("\n")
            sys.exit(1)
        except Exception as err:
            ARP.ErrorHandler().printToLog("\nError: Incorrect Username/Password, try again\n"
                        , err, ARP.ErrorHandler().getLogFile())
            print("\n . . . \n")
        else:
            login = False
    # load page for bid adjustments
    AutoRP_obj.openBidAdjustments()
    ARP.browser.execute_script("revPieBidAdjustments('396', 'RP_102_11am to 7pm')")

    ARP.ErrorHandler().waiting(3)
    ARP.browser.execute_script("changeBidAdjustmentsDateFilter('all')")
    ARP.ErrorHandler().waiting(10)
    check = True
    while check:
        if (str(ARP.browser.find_element_by_id(
                'bidAdjustmentsDateFilter').get_attribute(
                        "value")) == "all"):
            check = False
        else:
            ARP.ErrorHandler().checkBrowser()
    Bids = BidAdjuster.copyBids()
    sourceIDs = Bids[0]
    WebDriverWait(ARP.browser, 15).until(
            expected_conditions.presence_of_element_located(
                    (By.ID, 'bidAdjustmentsTable')))
    for index, item in enumerate(sourceIDs):
        _customBidID = r"customBid_" + str(item)
        print(_customBidID)
        ARP.ErrorHandler().waiting(1)
        try:
            text_area = ARP.browser.find_element_by_id(_customBidID)
        except:pass
        else:
            if Bids[2][index] != "0.01" and item != "1332" and item !="1250" and item != "1252" and item != "580" and item != "518" and item != "536" and item != "383":
                text_area.send_keys(Keys.CONTROL, 'a')
                ARP.ErrorHandler().waiting(1)
                text_area.send_keys("0.01")
                ARP.ErrorHandler().waiting(1)
                ARP.browser.execute_script("makeCustomBidAdjustment('" + str(item) + "')")
except KeyboardInterrupt:
    print("\n")
    sys.exit(1)
except Exception as err:
    ARP.ErrorHandler().printToLog("\n\nError while loading tabs, closing...\n"
                , err, ARP.ErrorHandler().getLogFile())
    ARP.browser.quit()
    sys.exit(1)


