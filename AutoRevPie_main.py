#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May  8 09:41:43 2019

@author: bryan
"""

import configparser

import ARP_setup as ARP

###############################################################################
# Program start...

with open(ARP.AutomateRP.Browser.Config.getfpath(__file__)+"/AutoRevPie.info", 'r') as f:
    print(" . . . ", f.readline())
print("\nloading . . . \n")

try: # write heading to logs file if does not exist already
    _existingFile = ARP.AutomateRP.Browser.Config.os.path.isfile(ARP.AutomateRP.Browser.ErrorHandler().getLogFile())
    if not _existingFile:
        with open(ARP.AutomateRP.Browser.ErrorHandler().getLogFile(), 'a') as f:
            print('Filename:', ARP.AutomateRP.Browser.ErrorHandler().getLogFile(), file=f)
            print('\n - - - Logs (' + str(ARP.AutomateRP.time.strftime("%Y-%m-%d %H:%M.%S")) + ')' + ' - - - ' + '\n\n', file=f)
            _loop = False
except KeyboardInterrupt:
    print("\n")
    ARP.AutomateRP.Browser.Config.sys.exit(1)
except Exception:pass

################################ CONFIG #######################################
# CONFIG FILE SHOULD BE IN THE WORKING DIRECTORY

# get config file
try:
    # open file
    configParser = configparser.RawConfigParser()
    configParser.read_file(open(ARP.AutomateRP.Browser.Config.getfpath(__file__)
                            + "/config.txt"))
    # save to variables
    admin = r"{}".format(configParser.get('website-urls', 'admin'))
    wallboard = r"{}".format(configParser.get('website-urls', 'wallboard'))
    queueDetails = r"{}".format(configParser.get('website-urls', 'queueDetails'))
    queue_uname = r"{}".format(configParser.get('login-info', 'username'))
    queue_pass = r"{}".format(configParser.get('login-info', 'password'))
except KeyboardInterrupt:
    print("\n")
    ARP.AutomateRP.Browser.Config.sys.exit(1)
except Exception as err:
    ARP.AutomateRP.Browser.ErrorHandler().printToLog("\n\nconfigParser: Error while reading config file 'config.txt', closing..."
                , err, ARP.AutomateRP.Browser.ErrorHandler().getLogFile())
    ARP.AutomateRP.Browser.Config.sys.exit(1)

############################# browser setup ###################################

AutoRP_obj = ARP.AutomateRP.AutoRevPie(admin, 0, 1)
RepCounter = ARP.AutomateRP.RepCount(2)
CampaignStats = ARP.AutomateRP.RevPieStats(3, ARP.AutomateRP.Browser)

try:
    # load wallboard
    ARP.AutomateRP.Browser.browser.get(wallboard)
    ARP.AutomateRP.Browser.ErrorHandler().waiting(1)
    ARP.AutomateRP.Browser.queueDaddy_login(queue_uname, queue_pass)
    ARP.AutomateRP.Browser.ErrorHandler().waiting(1)
    # load admin page
    ARP.AutomateRP.Browser.browser.execute_script("window.open('" + admin + "')")
    # login to admin
    ARP.AutomateRP.Browser.ErrorHandler().waiting(1)
    ARP.AutomateRP.Browser.ErrorHandler().switchToTab(AutoRP_obj.bidsPageTab)
    _loop = True
    while _loop:
        try:
            _loop = ARP.AutomateRP.Browser.ErrorHandler().checkBrowser()
            ARP.AutomateRP.Browser.admin_login(ARP.AutomateRP.Browser.getLoginInfo('-u'), ARP.AutomateRP.Browser.getLoginInfo('-p'))
        except KeyboardInterrupt:
            print("\n")
            ARP.AutomateRP.Browser.Config.sys.exit(1)
        except Exception as err:
            ARP.AutomateRP.Browser.ErrorHandler().printToLog("\nError: Incorrect Username/Password, try again...\n"
                        , err, ARP.AutomateRP.Browser.ErrorHandler().getLogFile())
            print("\n . . . \n")
        else:
            _loop = False
    # load page for bid adjustments
    AutoRP_obj.openBidAdjustments()
    AutoRP_obj.getCampaignStatus()
    # get initial rep count
    ARP.AutomateRP.Browser.ErrorHandler().waiting(1)
    ARP.AutomateRP.Browser.browser.execute_script("window.open('" + admin + "')")
    ARP.AutomateRP.Browser.ErrorHandler().switchToTab(RepCounter.queueOrderTab)
    repsAvail = RepCounter.getRepsMain()
    # load campaign performance page
    ARP.AutomateRP.Browser.browser.execute_script("window.open('" + admin + "/Affiliates/RevPieCampaignPerformance')")
    ARP.AutomateRP.Browser.ErrorHandler().switchToTab(CampaignStats.revpieStatsTab)
    ARP.AutomateRP.Browser.ErrorHandler().waiting(1)
except KeyboardInterrupt:
    print("\n")
    ARP.AutomateRP.Browser.Config.sys.exit(1)
except Exception as err:
    ARP.AutomateRP.Browser.ErrorHandler().printToLog("\n\nError while loading tabs, closing...\n"
                , err, ARP.AutomateRP.Browser.ErrorHandler().getLogFile())
    ARP.AutomateRP.Browser.browser.quit()
    ARP.AutomateRP.Browser.Config.sys.exit(1)

############################### - MAIN - ######################################

_loop = True
while _loop:
    _loop = ARP.AutomateRP.Browser.ErrorHandler().checkBrowser()
    try:
        AutoRP_obj.autoRevPie(RepCounter.repCount)
    except KeyboardInterrupt:
        print("\n")
        ARP.AutomateRP.Browser.Config.sys.exit(1)
    except Exception as err:
        ARP.AutomateRP.Browser.ErrorHandler().printToLog("\n\nError: error while executing AutoRevPie, closing...\n"
                    , err, ARP.AutomateRP.Browser.ErrorHandler().getLogFile())
        ARP.AutomateRP.Browser.browser.quit()
        ARP.AutomateRP.Browser.Config.sys.exit(1)
    # update revpieStats on every 5th minute of the hour...
    if ARP.AutomateRP.datetime.datetime.now().minute % 5 == 0:
        _startTime = ARP.AutomateRP.datetime.datetime.now().minute
        # also update queue order if 10th minute of the hour...
        if ARP.AutomateRP.datetime.datetime.now().minute % 10 == 0:
            try:
                ARP.AutomateRP.Browser.ErrorHandler().waiting(1)
                RepCounter.repCount = RepCounter.getRepsUpdate()
                ARP.AutomateRP.Browser.ErrorHandler().waiting(1)
                CampaignStats.getStatsUpdate(AutoRP_obj.currentCampaign
                                            , AutoRP_obj.campaigns[AutoRP_obj.currentCampaign][0])
                CampaignStats.output_stats()
                _wait = True
                while _wait:
                    if ARP.AutomateRP.datetime.datetime.now().minute == (_startTime + 1):
                        _wait = False
                    ARP.AutomateRP.Browser.ErrorHandler().waiting(1)
                    AutoRP_obj.autoRevPie(RepCounter.repCount)
            except KeyboardInterrupt:
                print("\n")
                ARP.AutomateRP.Browser.Config.sys.exit(1)
            except Exception as err:
                ARP.AutomateRP.Browser.ErrorHandler().printToLog("\n\nError while updating stats..."
                , err, ARP.AutomateRP.Browser.ErrorHandler().getLogFile())
        else: # else just get revpieStats
            try:
                CampaignStats.getStatsUpdate(AutoRP_obj.currentCampaign
                                            , AutoRP_obj.campaigns[AutoRP_obj.currentCampaign][0])
                CampaignStats.output_stats()
                ARP.AutomateRP.Browser.ErrorHandler().waiting(1)
                _wait = True
                while _wait:
                    if ARP.AutomateRP.datetime.datetime.now().minute == (_startTime + 1):
                        _wait = False
                    ARP.AutomateRP.Browser.ErrorHandler().waiting(1)
                    AutoRP_obj.autoRevPie(RepCounter.repCount)
            except KeyboardInterrupt:
                print("\n")
                ARP.AutomateRP.Browser.Config.sys.exit(1)
            except Exception as err:
                ARP.AutomateRP.Browser.ErrorHandler().printToLog("\n\nError: unable to update revpieStats..."
                , err, ARP.AutomateRP.Browser.ErrorHandler().getLogFile())


