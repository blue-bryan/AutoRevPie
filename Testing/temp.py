#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May  8 09:41:43 2019

@author: bryan
"""

import sys
import time
import datetime
import configparser

import setup
import AutomateRevPie.Automate_RevPie as ARP
import AutomateRevPie.RevPieStats as RP_Stats

###############################################################################
# Program start...

with open(ARP.Browser.Config.getfpath(__file__)+"/AutoRevPie.info", 'r') as f:
    print(" . . . ", f.readline())
print("\nloading . . . \n")

try: # write heading to logs file if does not exist already
    _existingFile = ARP.Browser.Config.os.path.isfile(ARP.Browser.ErrorHandler().getLogFile())
    if not _existingFile:
        with open(ARP.Browser.ErrorHandler().getLogFile(), 'a') as f:
            print('Filename:', ARP.Browser.ErrorHandler().getLogFile(), file=f)
            print('\n - - - Logs (' + str(time.strftime("%Y-%m-%d %H:%M.%S")) + ')' + ' - - - ' + '\n\n', file=f)
            _loop = False
except KeyboardInterrupt:
    print("\n")
    sys.exit(1)
except Exception:pass

################################ CONFIG #######################################
# CONFIG FILE SHOULD BE IN THE WORKING DIRECTORY

# get config file
try:
    # open file
    configParser = configparser.RawConfigParser()
    configParser.read_file(open(ARP.Browser.Config.getfpath(__file__)
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
    ARP.Browser.ErrorHandler().printToLog("\n\nconfigParser: Error while reading config file 'config.txt', closing..."
                , err, ARP.Browser.ErrorHandler().getLogFile())
    sys.exit(1)

############################# browser setup ###################################

AutoRP_obj = ARP.AutoRevPie(admin, 0, 1)
RepCounter = ARP.RepCount(2)
CampaignStats = RP_Stats.RevPieStats(3, ARP.Browser)

try:
    # load wallboard
    ARP.Browser.browser.get(wallboard)
    ARP.Browser.ErrorHandler().waiting(1)
    ARP.Browser.queueDaddy_login(queue_uname, queue_pass)
    ARP.Browser.ErrorHandler().waiting(1)
    # load admin page
    ARP.Browser.browser.execute_script("window.open('" + admin + "')")
    # login to admin
    ARP.Browser.ErrorHandler().waiting(1)
    ARP.Browser.ErrorHandler().switchToTab(AutoRP_obj.bidsPageTab)
    _loop = True
    while _loop:
        try:
            _loop = ARP.Browser.ErrorHandler().checkBrowser()
            ARP.Browser.admin_login(ARP.Browser.getLoginInfo('-u'), ARP.Browser.getLoginInfo('-p'))
        except KeyboardInterrupt:
            print("\n")
            sys.exit(1)
        except Exception as err:
            ARP.Browser.ErrorHandler().printToLog("\nError: Incorrect Username/Password, try again...\n"
                        , err, ARP.Browser.ErrorHandler().getLogFile())
            print("\n . . . \n")
        else:
            _loop = False
    # load page for bid adjustments
    AutoRP_obj.openBidAdjustments()
    AutoRP_obj.getCampaignStatus()
    # get initial rep count
    ARP.Browser.ErrorHandler().waiting(1)
    ARP.Browser.browser.execute_script("window.open('" + admin + "')")
    ARP.Browser.ErrorHandler().switchToTab(RepCounter.queueOrderTab)
    repsAvail = RepCounter.getRepsMain()
    # load campaign performance page
    ARP.Browser.browser.execute_script("window.open('" + admin + "/Affiliates/RevPieCampaignPerformance')")
    ARP.Browser.ErrorHandler().switchToTab(CampaignStats.revpieStatsTab)
    ARP.Browser.ErrorHandler().waiting(1)
    CampaignStats.getStatsPage(AutoRP_obj.currentCampaign
                                            , AutoRP_obj.campaigns[AutoRP_obj.currentCampaign][0])
except KeyboardInterrupt:
    print("\n")
    sys.exit(1)
except Exception as err:
    ARP.Browser.ErrorHandler().printToLog("\n\nError while loading tabs, closing...\n"
                , err, ARP.Browser.ErrorHandler().getLogFile())
    ARP.Browser.browser.quit()
    ARP.Browser.sys.exit(1)

############################### - MAIN - ######################################\

AutoRP_obj.currentCampaign = 1
AutoRP_obj.switchCampaigns( AutoRP_obj.campaigns[AutoRP_obj.currentCampaign-1][1]
                    , AutoRP_obj.campaigns[AutoRP_obj.currentCampaign-1][0]
                    , AutoRP_obj.campaigns[AutoRP_obj.currentCampaign][1]
                    , AutoRP_obj.campaigns[AutoRP_obj.currentCampaign][0])
