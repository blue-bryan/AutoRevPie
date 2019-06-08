#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May  8 09:41:43 2019

@author: bryan
"""

import traceback
import configparser
from getpass import getpass
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.common.exceptions import TimeoutException
import lxml.html
import datetime
import time
import sys
import os

###############################################################################
# CLASS DEFS:

class AutoPause:
    def __init__ (self):
        self.getReps = True
        self.isPaused = False
        self.adjustBids = 0
        self.totalCalls = 0
        self.callLimit = 10 # default callLimit
        self.repsToCalls = 0.20 # ratio to use for callLimit,
                                # x% of Reps in Queue = callLimit
        self.campaign1 = True # 8am-11am
        self.campaign2 = True # 11am-7pm
        self.campaign3 = True # 7pm-close
        
    def printIsPaused(self, isPaused):
        if self.isPaused:
            print('\nCampaign is currently: Paused\n\n')
            return(self.isPaused)
        else:
            print('\nCampaign is currently: Active\n')
            return(self.isPaused)
        
    # Counts calls in queue
    def getCalls(self):
        switchToTab(wallboardTab)
        try: # switch to wall board for total calls
            WebDriverWait(browser, 15).until(
                    expected_conditions.presence_of_element_located(
                            (By.CLASS_NAME, 'container')))
            rollover = browser.find_element_by_id('queue_count10')
            seniorLoan1 = browser.find_element_by_id('queue_count16')
            seniorLoan2 = browser.find_element_by_id('queue_count25')
            # custServ = browser.find_element_by_id('queue_count2')
            self.totalCalls = (int(rollover.text)
            + int(seniorLoan1.text)
            + int(seniorLoan2.text))
            return(self.totalCalls)
        except Exception as err:
            printToLog("\n\nBrowser error: wallboard\n"
                        , err)
            self.totalCalls = 0
            checkBrowser()
            return(self.totalCalls)
    
    # Main Method in Class AutoPause
    def autoPause(self, repsAvail, isPaused):
        BidAdjuster = autoBidAdjust()
        checkBrowser()
        
        # check if repsAvail == None, this will avoid NaN error for callLimit
        if repsAvail is None and self.getReps:
            printToLog("\nError: failed to get rep count, default callLimit == 10...\n\n", "")
            self.getReps = False
        elif repsAvail is 0 and self.getReps:
            printToLog("\nError: failed to get rep count, default callLimit == 10...\n\n", "")
            self.getReps = False
        elif repsAvail is not None and self.getReps:
            self.callLimit = round((repsAvail * self.repsToCalls), 0)
            self.getReps = True
        elif repsAvail is not None and self.getReps is False:
            if repsAvail > 0:
                self.getReps = True

        try:
            # update calls
            self.totalCalls = self.getCalls()
            # output
            print('\r' + ' Reps: ' + str(repsAvail) + '  Call Limit: ', self.callLimit
                  , '  Total Calls: ', self.totalCalls, ' '
                  , end="", flush = True)
        except Exception as err:
            printToLog("\n\nautoPause: Error while printing output\n"
                        , err)
            sys.exit(1)
        
        if (datetime.datetime.now().time() > datetime.datetime.strptime("08:59", "%H:%M").time()
        and datetime.datetime.now().time() < datetime.datetime.strptime("09:01", "%H:%M").time()
        and datetime.datetime.today().weekday() < 5):
            if self.isPaused:
                switchToTab(bidsPageTab)
                browser.execute_script("changeRevPieCampaignStatus(390, 0)")
                printToLog('\n\n9am-11am Campaign started\n', "")
                self.isPaused = self.getCampaignStatus()
        elif (datetime.datetime.now().time() > datetime.datetime.strptime("09:01", "%H:%M").time()
        and datetime.datetime.now().time() < datetime.datetime.strptime("11:00", "%H:%M").time()
        and datetime.datetime.today().weekday() < 5):
            if self.totalCalls > self.callLimit and not self.isPaused:
                self.isPaused = self.getCampaignStatus()
                if not self.isPaused and self.adjustBids == 0:
                    switchToTab(bidsPageTab)
                    waiting(1)
                    browser.execute_script("revPieBidAdjustments(390, 'RP101_8am_to_11am')")
                    waiting(2)
                    BidAdjuster.lowerBids()
                    waiting(1)
                    browser.execute_script("$.Dialog.close()")
                    # browser.execute_script("changeRevPieCampaignStatus(390, 1)")
                    printToLog('\n\n9am-11am Campaign Paused\n', "")
                    self.adjustBids = 1
                    self.isPaused = self.getCampaignStatus()
            elif self.totalCalls < 3 and self.isPaused:
                self.isPaused = self.getCampaignStatus()
                if self.isPaused:
                    switchToTab(bidsPageTab)
                    browser.execute_script("changeRevPieCampaignStatus(390, 0)")
                    printToLog('\n\n9am-11am Campaign un-paused...\n', "")
                elif self.adjustBids == 1:
                    waiting(1)
                    browser.execute_script("revPieBidAdjustments(390, 'RP101_8am_to_11am')")
                    waiting(2)
                    BidAdjuster.raiseBids()
                    waiting(1)
                    browser.execute_script("$.Dialog.close()")
                    self.adjustBids = 0
                    self.isPaused = self.getCampaignStatus()
        elif (datetime.datetime.now().time() > datetime.datetime.strptime("11:01", "%H:%M").time()
        and datetime.datetime.now().time() < datetime.datetime.strptime("11:02", "%H:%M").time()
        and datetime.datetime.today().weekday() < 5):
                switchToTab(bidsPageTab)
                browser.execute_script("changeRevPieCampaignStatus(390, 1)")
                waiting(1)
                browser.execute_script("changeRevPieCampaignStatus(396, 0)")
                waiting(2)
                browser.execute_script("revPieBidAdjustments(390, 'RP101_8am_to_11am')")
                waiting(1)
                WebDriverWait(browser, 15).until(
                        expected_conditions.presence_of_element_located(
                                (By.ID,'bidAdjustmentsTable')))
                waiting(1)
                BidAdjuster.copyBids()
                waiting(1)
                browser.execute_script("$.Dialog.close()")
                waiting(3)
                browser.execute_script("revPieBidAdjustments(396, 'RP_102_11am to 7pm')")
                waiting(1)
                BidAdjuster.pasteBids()
                waiting(1)
                browser.execute_script("$.Dialog.close()")
                printToLog('\n\nSwitched to 11am campaign\n', "")
                # wait until 11:02
                waiting(60)
        elif (datetime.datetime.now().time() > datetime.datetime.strptime("11:02", "%H:%M").time()
        and datetime.datetime.now().time() < datetime.datetime.strptime("19:00", "%H:%M").time()
        and datetime.datetime.today().weekday() < 5):
            if self.totalCalls > self.callLimit and not self.isPaused:
                self.isPaused = self.getCampaignStatus()
                if not self.isPaused and self.adjustBids == 0:
                    switchToTab(bidsPageTab)
                    waiting(1)
                    browser.execute_script("revPieBidAdjustments(390, 'RP101_8am_to_11am')")
                    waiting(2)
                    BidAdjuster.lowerBids()
                    waiting(1)
                    browser.execute_script("$.Dialog.close()")
                    # browser.execute_script("changeRevPieCampaignStatus(396, 1)")
                    self.isPaused = self.getCampaignStatus()
                    printToLog('\n\n11am-7pm Campaign Paused\n', "")
            elif self.totalCalls < 3:
                if self.isPaused:
                    self.isPaused = self.getCampaignStatus()
                    if self.isPaused:
                        switchToTab(bidsPageTab)
                        browser.execute_script("changeRevPieCampaignStatus(396, 0)")
                        printToLog('\n\n11am-7pm Campaign un-paused...\n', "")
                        self.isPaused = self.getCampaignStatus()
                    waiting(1)                
                    self.isPaused = self.getCampaignStatus()
        elif (datetime.datetime.now().time() > datetime.datetime.strptime("19:01", "%H:%M").time()
        and datetime.datetime.now().time() < datetime.datetime.strptime("19:02", "%H:%M").time()
        and datetime.datetime.today().weekday() < 5):
                switchToTab(bidsPageTab)
                browser.execute_script("changeRevPieCampaignStatus(396, 1)")
                waiting(1)
                browser.execute_script("changeRevPieCampaignStatus(391, 0)")
                waiting(2)
                browser.execute_script("revPieBidAdjustments(396, 'RP_102_11am to 7pm')")
                waiting(1)
                WebDriverWait(browser, 15).until(
                        expected_conditions.presence_of_element_located(
                                (By.ID,'bidAdjustmentsTable')))
                waiting(1)
                BidAdjuster.copyBids()
                waiting(1)
                browser.execute_script("$.Dialog.close()")
                waiting(3)
                browser.execute_script("revPieBidAdjustments(391, 'RP_103_7pmClose')")
                waiting(1)
                BidAdjuster.pasteBids()
                waiting(1)
                browser.execute_script("$.Dialog.close()")
                printToLog('\n\nSwitched to 7pm campaign\n', "")
                # wait until 19:02
                waiting(60)
        elif (datetime.datetime.now().time() > datetime.datetime.strptime("19:00", "%H:%M").time()
        and datetime.datetime.now().time() < datetime.datetime.strptime("21:00", "%H:%M").time()
        and datetime.datetime.today().weekday() < 5):
            if self.totalCalls > self.callLimit:
                self.isPaused = self.getCampaignStatus()
                if not self.isPaused:
                    switchToTab(bidsPageTab)
                    browser.execute_script("changeRevPieCampaignStatus(391, 1)")
                    self.isPaused = self.getCampaignStatus()
                    printToLog('\n\n7pm-close Campaign Paused\n', "")
            elif self.totalCalls < 3:
                if self.isPaused:
                    self.isPaused = self.getCampaignStatus()
                    if self.isPaused:
                        switchToTab(bidsPageTab)
                        browser.execute_script("changeRevPieCampaignStatus(391, 0)")
                        self.isPaused = self.getCampaignStatus()
                        printToLog('\n\n7pm-close Campaign un-paused...\n', "")
        elif (datetime.datetime.now().time() > datetime.datetime.strptime("21:00", "%H:%M").time()
        and datetime.datetime.now().time() < datetime.datetime.strptime("21:01", "%H:%M").time()
        and datetime.datetime.today().weekday() < 5):
            browser.execute_script("changeRevPieCampaignStatus(391, 1)")
            self.isPaused = self.getCampaignStatus()
            printToLog('\n\n7pm-close Campaign Paused\n', "")

    def getCampaignStatus(self):
        switchToTab(revpieTableTab)
        try:
            WebDriverWait(browser, 15).until(
                    expected_conditions.presence_of_element_located(
                            (By.ID, "revPieCampaignsDiv")))
        except Exception as err:
            printToLog("\n\nBrowser Error while getting campaign status, closing...\n"
                        , err)
            checkBrowser()
            return(False)
        else:
            browser.refresh()
            try:
                WebDriverWait(browser, 15).until(
                        expected_conditions.presence_of_element_located(
                                (By.ID, "revPieCampaignsDiv")))
            except Exception as err:
                printToLog("\n\ngetCampaignStatus: error, cannot find 'revPieCampaignsDiv'"
                           , err)
                return(False)
            else:
                # get the table
                now = datetime.datetime.now()
                table =  browser.find_element_by_xpath(
                        "//table[@class='table striped nbm bordered hovered']")
                tableValues = []
                for i in table.find_elements_by_tag_name('span'):
                    tableValues.append(i.text) 
                # iterate over all the rows    
                for index, item in enumerate(tableValues):
                        if item == "RP101_8am_to_11am":
                            if tableValues[index+2] == "paused":
                                self.campaign1 = True
                            else:
                                self.campaign1 = False
                        if item == "RP_102_11am to 7pm":
                            if tableValues[index+2] == "paused":
                                self.campaign2 = True
                            else:
                                self.campaign2 = False
                        if item == "RP_103_7pmClose":
                            if tableValues[index+2] == "paused":
                                self.campaign3 = True
                            else:
                                self.campaign3 = False
                if (now.time() > datetime.datetime.strptime("08:59", "%H:%M").time()
                and now.time() < datetime.datetime.strptime("11:00", "%H:%M").time()):
                    if self.campaign1:
                        self.isPaused = True
                    elif not self.campaign1:
                        self.isPaused = False
                elif (now.time() > datetime.datetime.strptime("11:00", "%H:%M").time()
                and now.time() < datetime.datetime.strptime("19:00", "%H:%M").time()):
                    if self.campaign2:
                        self.isPaused = True
                    elif not self.campaign2:
                        self.isPaused = False
                elif (now.time() > datetime.datetime.strptime("19:00", "%H:%M").time()
                and now.time() < datetime.datetime.strptime("21:00", "%H:%M").time()):
                    if self.campaign3:
                        self.isPaused = True
                    elif not self.campaign3:
                        self.isPaused = False
                return(self.isPaused)

class RepCount:
    def __init__ (self):
        self.repCount = 0
        
    def getRepsMain(self):
        try:
            # load wallboard
            browser.execute_script("window.open('" + queueDetails + "')")
            switchToTab(1)
            waiting(1)
            self.repCount = self.getRepsUpdate()
        except KeyboardInterrupt:
            print("")
            sys.exit(1)
        except Exception as err:
            printToLog("\n\ngetRepsMain: error, closing...\n"
                       , err)
            sys.exit(1)
        return(self.repCount)

    def getRepsUpdate(self):
        try:
            # wait for element
            WebDriverWait(browser, 20).until(
                    expected_conditions.presence_of_element_located(
                            (By.XPATH, "//div[@class='ext-overlay']")))
            # get list of all reps by phone extension
            tableA = browser.find_elements(By.XPATH, "//div[@class='ext-overlay']")
            x = len(tableA) # get count
            # wait for element
            WebDriverWait(browser, 20).until(
                    expected_conditions.presence_of_element_located(
                            (By.XPATH, "//i[@class='glyphicon glyphicon-option-horizontal']")))
            # get list of all reps on dnd
            tableB = browser.find_elements(By.XPATH, "//i[@class='glyphicon glyphicon-option-horizontal']")
            y = len(tableB) # get count
            self.repCount = ((x - y) + 1) # add 1 to offset 0 indexing
            return(self.repCount)
        except KeyboardInterrupt:
            print("\n")
            sys.exit(1)
        except Exception as err:
            printToLog("\n\ngetRepsUpdate Error: Failed to get repCount...\n"
                       , err)
            return(None)

class autoBidAdjust:
    def __init__(self):
        self.sourceIDs = []
        self.customBids = []

    def copyBids(self):
        # wait for the table
        waiting(1)
        WebDriverWait(browser, 15).until(
                expected_conditions.presence_of_element_located(
                        (By.ID,'bidAdjustmentsTable')))
        # get the table
        data = BeautifulSoup(browser.page_source, "lxml")
        root = lxml.html.fromstring(browser.page_source)
        table = root.xpath("//table[@class='table striped nbm bordered']")[0]
        # iterate over all the rows
        tableValues = []
        for td in table.xpath('.//td'):
            tableValues.append(td.text)
        self.sourceIDs.append(tableValues[::7])
        waiting(1)
        for index in range(len(self.sourceIDs[0])):
            _customBidID = r"customBid_" + str(self.sourceIDs[0][index])
            try:
                output = data.find("input", {"id": _customBidID})['value']
                self.customBids.append(output)
            except:pass
        return(self.sourceIDs[0], self.customBids)

    def pasteBids(self):
        sourceIDs = self.sourceIDs[0]
        customBids = self.customBids
        browser.execute_script("changeBidAdjustmentsDateFilter('last_week')")
        waiting(1)
        loop = True
        while loop:
            if (str(browser.find_element_by_id(
                    'bidAdjustmentsDateFilter').get_attribute(
                            "value")) == "last_week"):
                loop = False
            else:
                checkBrowser()
        for index, item in enumerate(sourceIDs):
            _customBidID = r"customBid_" + str(item)
            WebDriverWait(browser, 15).until(
                    expected_conditions.presence_of_element_located(
                            (By.ID, 'bidAdjustmentsTable')))
            try:
                text_area = browser.find_element_by_id(_customBidID)
                text_area.send_keys(Keys.CONTROL, 'a')
                waiting(1)
                text_area.send_keys(str(customBids[index]))
                waiting(1)
                browser.execute_script("makeCustomBidAdjustment('" + str(item) + "')")
            except:pass # will pass if the sourceID is not available

    def lowerBids(self):
        waiting(1)
        sourceIDs = self.sourceIDs[0]
        customBids = self.customBids
        for index, item in enumerate(sourceIDs):
            _customBidID = r"customBid_" + str(item)
            WebDriverWait(browser, 15).until(
                    expected_conditions.presence_of_element_located(
                            (By.ID, 'bidAdjustmentsTable')))
            try:
                text_area = browser.find_element_by_id(_customBidID)
                text_area.send_keys(Keys.CONTROL, 'a')
                waiting(1)
                _newBid = float(customBids[index]) - 0.10
                text_area.send_keys(str(_newBid))
                waiting(1)
                browser.execute_script("makeCustomBidAdjustment('" + str(item) + "')")
            except:pass # will pass if the sourceID is not available

    def raiseBids(self):
        waiting(1)
        try:
            sourceIDs = self.sourceIDs[0]
            customBids = self.customBids
        except:pass # silent fail if no previous values stored, i.e copyBids() was not called
        else:
            for index, item in enumerate(sourceIDs):
                _customBidID = r"customBid_" + str(item)
                WebDriverWait(browser, 15).until(
                        expected_conditions.presence_of_element_located(
                                (By.ID, 'bidAdjustmentsTable')))
                try:
                    text_area = browser.find_element_by_id(_customBidID)
                    text_area.send_keys(Keys.CONTROL, 'a')
                    waiting(1)
                    _newBid = float(customBids[index]) + 0.10
                    text_area.send_keys(str(_newBid))
                    waiting(1)
                    browser.execute_script("makeCustomBidAdjustment('" + str(item) + "')")
                except:pass # will pass if the sourceID is not available

# ---END OF CLASS DEFS---
###############################################################################
# FUNCTION DEFS:

def start_browser():
    # webdriver setup
    try:
        options = webdriver.FirefoxOptions()
        options.headless = False
        options.add_argument('--ignore-certificate-errors')
        options.add_argument("--test-type")
        options.binary_location = "/usr/bin/firefox"
        browser = webdriver.Firefox(options=options)
        browser.set_window_size(1920, 1080)
        return(browser)
    except Exception as err:
        printToLog("\n\nWebDriver: Error on browser setup"
                    , err)
        sys.exit(1)

def admin_login(username, password):
    try:
        wait = WebDriverWait(browser, 15)
        wait.until(
                expected_conditions.presence_of_element_located(
                        (By.ID, "UserName")))
    except Exception as err:
        printToLog("\nBrowser Error: failed to login to admin, closing..."
                   , err)
        checkBrowser()
        sys.exit(1)
    else:
        # type credentials
        text_area = browser.find_element_by_css_selector('#UserName')
        text_area.send_keys(username)
        text_area = browser.find_element_by_id('Password')
        text_area.send_keys(password)
        # click log in button
        browser.find_element_by_xpath("//input[@type='submit' and @value='Log in']").click()
        WebDriverWait(browser, 15).until(
                expected_conditions.presence_of_element_located(
                        (By.ID, 'formId')))
        # skip seat selection
        browser.execute_script("window.location = '/skipseat1234'")
        waiting(1)

def queueDaddy_login(username, password):
    try:
        wait = WebDriverWait(browser, 15)
        wait.until(
                expected_conditions.presence_of_element_located(
                        (By.XPATH, "//input[@name='userName']")))
    except Exception as err:
        printToLog("\nBrowser Error: failed to login to QueueDaddy, closing..."
                  , err)
        checkBrowser()
        sys.exit(1)
    else:
        text_area = browser.find_element_by_xpath("//input[@name='userName']")
        text_area.send_keys(username)
        text_area = browser.find_element_by_xpath("//input[@name='passWord']")
        text_area.send_keys(password)

        browser.find_element_by_xpath("//button[@value='Submit']").click()
        waiting(1)

def openBidAdjustments():
    try:
        wait = WebDriverWait(browser, 30)
        browser.get(admin + "/Maintenance")
        wait.until(
                expected_conditions.presence_of_element_located(
                        (By.XPATH, "//a[.='RevPie Reporting']")))
        accordionFrame = browser.find_element_by_xpath("//a[.='RevPie Reporting']")
        actions = ActionChains(browser)
        actions.move_to_element(accordionFrame).click().perform()
        waiting(2)
        browser.execute_script("$('#RevPieCampaigns').click()")
        wait.until(
                expected_conditions.presence_of_element_located(
                        (By.ID, "revPieCampaignsDiv")))
    except Exception as err:
        printToLog("\n\nBrowser Error: failed to open Bid Adjustments, closing...\n"
                    , err)
        checkBrowser()
        
def waiting(duration):
    try:
        time.sleep(duration)
    except KeyboardInterrupt as err:
        printToLog("\n"
                    , err)
        checkBrowser()

def sleep_until(target):
    now = datetime.datetime.now()
    delta = target - now

    if delta > datetime.timedelta(0):
        time.sleep(delta.total_seconds())

def switchToTab(tab):
    try:
        waiting(1)
        browser.switch_to.window(browser.window_handles[tab])
    except Exception as err:
        printToLog("\n\n\nswitchTabs: Error while switching tabs, closing...\n"
                    , err)
    except KeyboardInterrupt as err:
        printToLog("\n"
                    , err)
        checkBrowser()

def getFilename(filename):
    __location__ = os.path.realpath(
            os.path.join(os.getcwd(), os.path.dirname(__file__)))
    fpath = os.path.join(__location__, filename)
    return(fpath)

def checkBrowser():
    try:
        browser.title
    except Exception as err:
        printToLog("\n\ncheckBrowser: Error, closing...\n"
                   , err)
        try:
            browser.quit()
            sys.exit(1)
            return(False)
        except:
            sys.exit(1)
    else:
        return(True)

def openLog():
    filename = getFilename("logs.txt")
    # open log file and print header to file
    with open(filename, 'w') as f:
        print('Filename:', filename, file=f)
        print('\n\nLogs (' + str(time.strftime("%Y-%m-%d %H:%M.%S"))
        + ')\n------\n', file=f)

def printToLog(message,err):
    # print message to screen
    print(message)
    # print error message to file with timestamp and Exception
    filename = getFilename("logs.txt")
    with open(filename, 'a') as f:
        print(datetime.datetime.now(), '-', message, file=f)
        print(str(err), file=f)
        print(traceback.format_exc(), file=f)
# ---END OF FUNC DEFS---
###############################################################################

print("\n####################################################################\n")
      
# Open log file 'log.txt' for logging
try:
    openLog()
except KeyboardInterrupt:
    sys.exit(1)
except Exception as err:
    printToLog("\n\nopenLog: Error while loading '/log.txt', logs will not be recorded\n"
                , err)
    sys.exit(1)

try:
    # input and store username & password
    admin_uname = input("\n Input Admin Username: ")
    admin_pass = getpass(prompt="  password: ")
    # admin_pass = input("  password: ")
    print("\n...\n")
except KeyboardInterrupt:
    print("\n")
    sys.exit(1)
except Exception as err:
    printToLog("\n\nError during user input, closing...\n"
                , err)
    sys.exit(1)

################################ CONFIG #######################################
# CONFIG FILE SHOULD BE IN THE WORKING DIRECTORY

# get config file
try:
    configParser = configparser.RawConfigParser()
    configParser.read_file(open(getFilename("config.txt")))
except Exception as err:
    printToLog("\n\nconfigParser: Error while openning 'config.txt', closing...\n"
                , err)
    sys.exit(1)
try:
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
    printToLog("\n\nconfigParser: Error while reading config file 'config.txt', closing..."
                , err)
    sys.exit(1)

############################# browser setup ###################################

browser = start_browser()
try:
    # load wallboard
    browser.get(wallboard)
    waiting(1)
    queueDaddy_login(queue_uname, queue_pass)
    waiting(1)
    # get initial rep count
    RepCounter = RepCount()
    repsAvail = RepCounter.getRepsMain()
    waiting(1)
    # load admin page
    browser.execute_script("window.open('" + admin + "')")
    # login to admin
    switchToTab(2)
    admin_login(admin_uname, admin_pass)
    # load reporting page for bid adjustments
    waiting(1)
    switchToTab(2)
    openBidAdjustments()
    # load tab for getCampaignStatus
    browser.execute_script("window.open('" + admin + "Affiliates/RevPieCampaigns')")
    waiting(1)
except Exception as err:
    printToLog("\n\nError while loading tabs, closing...\n"
                , err)
    sys.exit(1)
# save tabs to variables to be used with switchTabs() function
wallboardTab = 0
queueOrderTab = 1
bidsPageTab = 2
revpieTableTab = 3

############################### - MAIN - ######################################

AutoPauser = AutoPause()
AutoPauser.isPaused = AutoPauser.getCampaignStatus()
waiting(1)
AutoPauser.printIsPaused(AutoPauser.isPaused)

loop = True
while loop:
    # update queue order on every 10th minute of the hour
    if datetime.datetime.now().minute % 10 == 0:
        try: # if True, getRepsUpdate
            switchToTab(queueOrderTab)
            waiting(1)
            RepCounter.repCount = RepCounter.getRepsUpdate()
            waiting(1)
            for i in range(60):
                if i < 60:
                    AutoPauser.autoPause(RepCounter.repCount, AutoPauser.isPaused)
                    waiting(1)
        except Exception as err:
            printToLog("\n\nError: unable to update rep count..."
                , err)
    else:
        #try:
        AutoPauser.autoPause(RepCounter.repCount, AutoPauser.isPaused)
        #except Exception as e:
           # printToLog("\n\nError: error while executing autoPause, closing..."
           #            , e)
           # browser.quit()
           # sys.exit(1)
    loop = checkBrowser()


