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

with open(ARP.AutomateRP.Config.getfpath(__file__)+"/AutoRevPie.info", 'r') as f:
    print(" . . . ", f.readline())
print("\nloading . . . \n")

try: # write heading to logs file if does not exist already
    _existingFile = ARP.AutomateRP.Config.os.path.isfile(ARP.AutomateRP.EH.Handler().getLogFile())
    if not _existingFile:
        with open(ARP.AutomateRP.EH.Handler().getLogFile(), 'a') as f:
            print('Filename:', ARP.AutomateRP.EH.Handler().getLogFile(), file=f)
            print('\n - - - Logs (' + str(ARP.AutomateRP.time.strftime("%Y-%m-%d %H:%M.%S")) + ')' + ' - - - ' + '\n\n', file=f)
            _loop = False
except KeyboardInterrupt:
    print("\n")
    ARP.AutomateRP.Config.sys.exit(1)
except Exception:pass

################################ CONFIG #######################################
# CONFIG FILE SHOULD BE IN THE WORKING DIRECTORY

# get config file
try:
    # open file
    configParser = configparser.RawConfigParser()
    configParser.read_file(open(ARP.AutomateRP.Config.getfpath(__file__)
                            + "/config.txt"))
    # save to variables
    admin = r"{}".format(configParser.get('website-urls', 'admin'))
    wallboard = r"{}".format(configParser.get('website-urls', 'wallboard'))
    queueDetails = r"{}".format(configParser.get('website-urls', 'queueDetails'))
    queue_uname = r"{}".format(configParser.get('login-info', 'username'))
    queue_pass = r"{}".format(configParser.get('login-info', 'password'))
except KeyboardInterrupt:
    print("\n")
    ARP.AutomateRP.Config.sys.exit(1)
except Exception as err:
    ARP.AutomateRP.EH.Handler().printToLog("\n\nconfigParser: Error while reading config file 'config.txt', closing..."
                , err, ARP.AutomateRP.EH.Handler().getLogFile())
    ARP.AutomateRP.Config.sys.exit(1)

############################# browser setup ###################################

AutoRP_obj = ARP.AutomateRP.AutoRevPie(admin, 0, 1)
RepCounter = ARP.AutomateRP.RepCount(2, ARP.AutomateRP.Browser, ARP.AutomateRP.EH.Handler())
CampaignStats = ARP.AutomateRP.RevPieStats.RPStats(3, ARP.AutomateRP.Browser, ARP.AutomateRP.EH.Handler())

try:
    # load wallboard
    ARP.AutomateRP.Browser.browser.get(wallboard)
    ARP.AutomateRP.EH.Handler().waiting(1)
    ARP.AutomateRP.BrowserHandler().queueDaddy_login(queue_uname, queue_pass)
    ARP.AutomateRP.EH.Handler().waiting(1)
    # load admin page
    ARP.AutomateRP.Browser.browser.execute_script("window.open('" + admin + "')")
    # login to admin
    ARP.AutomateRP.EH.Handler().waiting(1)
    ARP.AutomateRP.BrowserHandler().switchToTab(AutoRP_obj.bidsPageTab)
    _loop = True
    while _loop:
        try:
            _loop = ARP.AutomateRP.BrowserHandler().checkBrowser()
            ARP.AutomateRP.BrowserHandler().admin_login(ARP.AutomateRP.BrowserHandler().getLoginInfo('-u'), ARP.AutomateRP.BrowserHandler().getLoginInfo('-p'))
        except KeyboardInterrupt:
            print("\n")
            ARP.AutomateRP.Config.sys.exit(1)
        except Exception as err:
            ARP.AutomateRP.EH.Handler().printToLog("\nError: Incorrect Username/Password, try again...\n"
                        , err, ARP.AutomateRP.EH.Handler().getLogFile())
            print("\n . . . \n")
        else:
            _loop = False
    # load page for bid adjustments
    AutoRP_obj.openBidAdjustments()
    AutoRP_obj.getCampaignStatus()
    # get initial rep count
    ARP.AutomateRP.EH.Handler().waiting(1)
    ARP.AutomateRP.Browser.browser.execute_script("window.open('" + admin + "')")
    ARP.AutomateRP.BrowserHandler().switchToTab(RepCounter.queueOrderTab)
    repsAvail = RepCounter.getRepsMain()
    # load campaign performance page
    ARP.AutomateRP.Browser.browser.execute_script("window.open('" + admin + "/Affiliates/RevPieCampaignPerformance')")
    ARP.AutomateRP.BrowserHandler().switchToTab(CampaignStats.revpieStatsTab)
    CampaignStats.getStatsPage(AutoRP_obj.currentCampaign
                            , AutoRP_obj.campaigns[AutoRP_obj.currentCampaign][0])
    ARP.AutomateRP.EH.Handler().waiting(1)
except KeyboardInterrupt:
    print("\n")
    ARP.AutomateRP.Config.sys.exit(1)
except Exception as err:
    ARP.AutomateRP.EH.Handler().printToLog("\n\nError while loading tabs, closing...\n"
                , err, ARP.AutomateRP.EH.Handler().getLogFile())
    ARP.AutomateRP.Browser.browser.quit()
    ARP.AutomateRP.Config.sys.exit(1)

############################### - MAIN - ######################################

_loop = True
while _loop:
    _loop = ARP.AutomateRP.BrowserHandler().checkBrowser()
    try:
        AutoRP_obj.autoRevPie(RepCounter.repCount)
    except KeyboardInterrupt:
        print("\n")
        ARP.AutomateRP.Config.sys.exit(1)
    except Exception as err:
        ARP.AutomateRP.EH.Handler().printToLog("\n\nError: error while executing AutoRevPie, closing...\n"
                    , err, ARP.AutomateRP.EH.Handler().getLogFile())
        ARP.AutomateRP.Browser.browser.quit()
        ARP.AutomateRP.Config.sys.exit(1)
    # update revpieStats on every 5th minute of the hour...
    if ARP.AutomateRP.datetime.datetime.now().minute % 5 == 0:
        _startTime = ARP.AutomateRP.datetime.datetime.now().minute
        # also update queue order if 10th minute of the hour...
        if ARP.AutomateRP.datetime.datetime.now().minute % 10 == 0:
            try:
                ARP.AutomateRP.EH.Handler().waiting(1)
                RepCounter.repCount = RepCounter.getRepsUpdate()
                ARP.AutomateRP.EH.Handler().waiting(1)
                CampaignStats.getStatsUpdate(AutoRP_obj.currentCampaign
                                            , AutoRP_obj.campaigns[AutoRP_obj.currentCampaign][0])
                CampaignStats.output_stats()
            except KeyboardInterrupt:
                print("\n")
                ARP.AutomateRP.Config.sys.exit(1)
            except Exception as err:
                ARP.AutomateRP.EH.Handler().printToLog("\n\nError while updating stats..."
                , err, ARP.AutomateRP.EH.Handler().getLogFile())
            _wait = True
            while _wait:
                if ARP.AutomateRP.datetime.datetime.now().minute == (_startTime + 1):
                    _wait = False
                ARP.AutomateRP.EH.Handler().waiting(1)
                AutoRP_obj.autoRevPie(RepCounter.repCount)
        else: # else just get revpieStats
            try:
                CampaignStats.getStatsUpdate(AutoRP_obj.currentCampaign
                                            , AutoRP_obj.campaigns[AutoRP_obj.currentCampaign][0])
                CampaignStats.output_stats()
                ARP.AutomateRP.EH.Handler().waiting(1)
            except KeyboardInterrupt:
                print("\n")
                ARP.AutomateRP.Config.sys.exit(1)
            except Exception as err:
                ARP.AutomateRP.EH.Handler().printToLog("\n\nError: unable to update revpieStats..."
                , err, ARP.AutomateRP.EH.Handler().getLogFile())
            _wait = True
            while _wait:
                if ARP.AutomateRP.datetime.datetime.now().minute == (_startTime + 1):
                    _wait = False
                ARP.AutomateRP.EH.Handler().waiting(1)
                AutoRP_obj.autoRevPie(RepCounter.repCount)


