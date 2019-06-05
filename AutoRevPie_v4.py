#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May  8 09:41:43 2019

@author: bryan
"""

import os
import sys
import time
import datetime
import configparser

import AutomateRevPie.AutomateRevPie as ARP
import AutomateRevPie.config as Config

def openLog():
    ''' Will open (or create a file if none exists),
        named 'logs.txt' in the working directory.
    '''
    # open log file and print header to file
    with open(Config.logs_path, 'w') as f:
        print('Filename:', Config.logs_path, file=f)
        print('\n - - - Logs (' + str(time.strftime("%Y-%m-%d %H:%M.%S")) + ')' + ' - - - ' + '\n\n', file=f)

###############################################################################
# Program start...

print("\n####################################################################\n")
print("\nloading . . . \n")

# Open log file 'logs.txt' for logging
try:
    openLog()
except KeyboardInterrupt:
    sys.exit(1)
except Exception as err:
    ARP.printToLog("\n\nopenLog: Error while loading '/logs.txt', logs will not be recorded\n"
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
    ARP.printToLog("\n\nconfigParser: Error while reading config file 'config.txt', closing..."
                , err, Config.logs_path)
    sys.exit(1)

############################# browser setup ###################################

AutoRP_obj = ARP.AutoRevPie(admin, 0, 1)
RepCounter = AutoRP_obj.RepCount(2)
CampaignStats = AutoRP_obj.RevPieStats(3)

try:
    # load wallboard
    ARP.browser.get(wallboard)
    ARP.waiting(1)
    ARP.queueDaddy_login(queue_uname, queue_pass)
    ARP.waiting(1)
    # load admin page
    ARP.browser.execute_script("window.open('" + admin + "')")
    # login to admin
    ARP.waiting(1)
    ARP.switchToTab(AutoRP_obj.bidsPageTab)
    _loop = True
    while _loop:
        try:
            _loop = ARP.checkBrowser()
            ARP.admin_login(ARP.getLoginInfo("-u"), ARP.getLoginInfo("-p"))
        except KeyboardInterrupt:
            print("\n")
            sys.exit(1)
        except Exception as err:
            ARP.printToLog("\nError: Incorrect Username/Password, try again...\n"
                        , err, Config.logs_path)
            print("\n . . . \n")
        else:
            _loop = False
    # load page for bid adjustments
    AutoRP_obj.openBidAdjustments()
    AutoRP_obj.getCampaignStatus()
    # get initial rep count
    ARP.waiting(1)
    ARP.browser.execute_script("window.open('" + admin + "')")
    ARP.switchToTab(RepCounter.queueOrderTab)
    repsAvail = RepCounter.getRepsMain()
    # load campaign performance page
    ARP.browser.execute_script("window.open('" + admin + "/Affiliates/RevPieCampaignPerformance')")
    ARP.switchToTab(CampaignStats.revpieStatsTab)
    ARP.waiting(1)
except KeyboardInterrupt:
    print("\n")
    sys.exit(1)
except Exception as err:
    ARP.printToLog("\n\nError while loading tabs, closing...\n"
                , err, Config.logs_path)
    ARP.browser.quit()
    sys.exit(1)

############################### - MAIN - ######################################

AutoRP_obj.printIsPaused()
_loop = True
while _loop:
    _loop = ARP.checkBrowser()
    try:
        AutoRP_obj.autoRevPie(RepCounter.repCount)
    except KeyboardInterrupt:
        print("\n")
        sys.exit(1)
    except Exception as err:
        ARP.printToLog("\n\nError: error while executing AutoRevPie, closing...\n"
                    , err, Config.logs_path)
        ARP.browser.quit()
        sys.exit(1)
    # update revpieStats on every 5th minute of the hour...
    if datetime.datetime.now().minute % 5 == 0:
        _startTime = datetime.datetime.now().minute
        # also update queue order if 10th minute of the hour...
        if datetime.datetime.now().minute % 10 == 0:
            try:
                ARP.waiting(1)
                RepCounter.repCount = RepCounter.getRepsUpdate()
                ARP.waiting(1)
                print('\n', CampaignStats.getStatsUpdate(AutoRP_obj.currentCampaign
                                                    , AutoRP_obj.campaigns[AutoRP_obj.currentCampaign][0]), '\n')
                _wait = True
                while _wait:
                    if datetime.datetime.now().minute == (_startTime + 1):
                        _wait = False
                    ARP.waiting(1)
                    AutoRP_obj.autoRevPie(RepCounter.repCount)
            except KeyboardInterrupt:
                print("\n")
                sys.exit(1)
            except Exception as err:
                ARP.printToLog("\n\nError: unable to update rep count..."
                , err, Config.logs_path)
        else: # else just get revpieStats
            try:
                print('\n', CampaignStats.getStatsUpdate(AutoRP_obj.currentCampaign
                                                    , AutoRP_obj.campaigns[AutoRP_obj.currentCampaign][0]), '\n')
                ARP.waiting(1)
                _wait = True
                while _wait:
                    if datetime.datetime.now().minute == (_startTime + 1):
                        _wait = False
                    ARP.waiting(1)
                    AutoRP_obj.autoRevPie(RepCounter.repCount)
            except KeyboardInterrupt:
                print("\n")
                sys.exit(1)
            except Exception as err:
                ARP.printToLog("\n\nError: unable to update revpieStats..."
                , err, Config.logs_path)


