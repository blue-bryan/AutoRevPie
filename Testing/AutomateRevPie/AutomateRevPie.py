#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-Created on Wed May  8 09:41:43 2019
-@author: bryan

-A modular library using Selenium WebDriver built to fully automate
 traffic monitoring and the bidding process for RevPie.
"""

import sys
import time
import datetime
import lxml.html
import traceback
from getpass import getpass
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.common.exceptions import TimeoutException

# get logs file path
import AutomateRevPie.config as Config
logsPath = None

#                       - AutomateRevPie Module -
###############################################################################

class AutoRevPie:
    ''' Contains methods and functions
        to automatically monitor and adjust RevPie Campaigns.
        
         methods:
    '''
    def __init__ (self, _adminURL, _wallboardTab, _bidsPageTab):
        self.admin = _adminURL
        self.wallboardTab = _wallboardTab
        self.bidsPageTab = _bidsPageTab
        self.getReps = True
        self.isPaused = False
        self.adjustBids_CallLimit  = 8 # default callLimit == 8
        self.repsToCallsRatio = 0.25 # ratio to use for callLimit...
                                     # x% of Reps in Queue = callLimit
        self.maxCallLimit = 11 # limit of number of calls before pausing campaign
        self.adjustBids = 0
        self.totalCalls = 0
        self.currentCampaign = 0
        self.campaigns = [ # [name, ID, status]
                           ["RP101_8am_to_11am", "390", True] 
                         , ["RP_102_11am to 7pm", "396", True]
                         , ["RP_103_7pmClose", "391", True] ]
        self.campaignStats = []

    def printIsPaused(self):
        ''' *
        '''
        if self.isPaused:
            print('\nCampaign is currently: Paused\n\n')
            return(self.isPaused)
        else:
            print('\nCampaign is currently: Active\n')
            return(self.isPaused)

    def openBidAdjustments(self):
        ''' *
        '''
        try:
            wait = WebDriverWait(browser, 30)
            browser.get(self.admin + "/Maintenance")
            wait.until(
                    expected_conditions.presence_of_element_located(
                            (By.XPATH, "//a[.='RevPie Reporting']")))
            accordionFrame = browser.find_element_by_xpath("//a[.='RevPie Reporting']")
            actions = ActionChains(browser)
            actions.move_to_element(accordionFrame).click().perform()
            ErrorHandler().waiting(2)
            browser.execute_script("$('#RevPieCampaigns').click()")
            wait.until(
                    expected_conditions.presence_of_element_located(
                            (By.ID, "revPieCampaignsDiv")))
        except Exception as err:
            ErrorHandler().printToLog("\n\nBrowser Error: failed to open Bid Adjustments, closing...\n"
                        , err, logsPath)
            ErrorHandler().checkBrowser()

    def getCampaignStatus(self):
        ''' Will iterate the RevPie Campaigns table and get
            the pause status of each campaign in the campaigns[] array,
            then returns the array.
            * paused==True/active==False
        '''
        ErrorHandler().switchToTab(self.bidsPageTab)
        try:
            WebDriverWait(browser, 15).until(
                    expected_conditions.presence_of_element_located(
                            (By.ID, "revPieCampaignsDiv")))
        except Exception as err:
            ErrorHandler().printToLog("\n\nBrowser Error while getting campaign status, closing...\n"
                        , err, logsPath)
            ErrorHandler().checkBrowser()
            return(False)
        else:
            browser.execute_script("$('#RevPieCampaigns').click()")
            try:
                WebDriverWait(browser, 15).until(
                        expected_conditions.presence_of_element_located(
                                (By.ID, "revPieCampaignsDiv")))
            except Exception as err:
                ErrorHandler().printToLog("\n\ngetCampaignStatus: error, cannot find 'revPieCampaignsDiv'\n"
                        , err, logsPath)
                return(False)
            else:
                # get the table
                table =  browser.find_element_by_xpath(
                        "//table[@class='table striped nbm bordered hovered']")
                tableValues = []
                for i in table.find_elements_by_tag_name('span'):
                    tableValues.append(i.text) 
                # iterate over all the rows
                for index, item in enumerate(tableValues):
                    if item == "RP101_8am_to_11am":
                        if tableValues[index+2] == "paused":
                            self.campaigns[0][2] = True
                        else:
                            self.campaigns[0][2] = False
                    elif item == "RP_102_11am to 7pm":
                        if tableValues[index+2] == "paused":
                            self.campaigns[1][2] = True
                        else:
                            self.campaigns[1][2] = False
                    elif item == "RP_103_7pmClose":
                        if tableValues[index+2] == "paused":
                            self.campaigns[2][2] = True
                        else:
                            self.campaigns[2][2] = False
            return(self.campaigns)

    def switchCampaigns(self, campaignID_1, campaignName_1, campaignID_2, campaignName_2):
        ''' -
            * usage:\n 
                AutoRevPie.switchCampaigns(AutoRevPie.campaigns[AutoRevPie.currentCampaign-1][1]
                                         , AutoRevPie.campaigns[AutoRevPie.currentCampaign-1][0]
                                         , AutoRevPie.campaigns[AutoRevPie.currentCampaign][1]
                                         , AutoRevPie.campaigns[AutoRevPie.currentCampaign][0])
        '''
        BidAdjuster = AutoRevPie.autoBidAdjust()
        ErrorHandler().switchToTab(self.bidsPageTab)
        #browser.execute_script("changeRevPieCampaignStatus(" + campaignID_1 + ", 1)")
        ErrorHandler().waiting(1)
        #browser.execute_script("changeRevPieCampaignStatus(" + campaignID_2 + ", 0)")
        ErrorHandler().waiting(2)
        browser.execute_script("revPieBidAdjustments("
                                + campaignID_1 + ", '" + campaignName_1 + "')")
        ErrorHandler().waiting(1)
        WebDriverWait(browser, 15).until(
                expected_conditions.presence_of_element_located(
                        (By.ID,'bidAdjustmentsTable')))
        ErrorHandler().waiting(1)
        Bids = BidAdjuster.copyBids()
        ErrorHandler().waiting(1)
        browser.execute_script("$.Dialog.close()")
        ErrorHandler().waiting(2)
        browser.execute_script("revPieBidAdjustments("
                                + campaignID_2 + ", '" + campaignName_2 + "')")
        ErrorHandler().waiting(5)
        BidAdjuster.changeBids(*Bids, _option='-p')
        ErrorHandler().waiting(1)
        browser.execute_script("$.Dialog.close()")

    def watchCalls(self, campaignID, campaignName):
        ''' Will make adjustments to RevPie campaign status
            and bids based on criteria.
            * Used in AutoRevPie() so current campaign
              can be assigned based on time conditions
        '''
        BidAdjuster = AutoRevPie.autoBidAdjust()
        if self.campaigns[self.currentCampaign][2]:
            self.isPaused = True
        elif not self.campaigns[self.currentCampaign][2]:
            self.isPaused = False
        if self.totalCalls > self.adjustBids_CallLimit and not self.isPaused and self.adjustBids == 0:
            if not self.isPaused:
                ErrorHandler().switchToTab(self.bidsPageTab)
                ErrorHandler().waiting(1)
                browser.execute_script("revPieBidAdjustments("
                                        + campaignID + ", '" + campaignName + "')")
                ErrorHandler().waiting(2)
                Bids = BidAdjuster.copyBids()
                ErrorHandler().waiting(1)
                BidAdjuster.changeBids(*Bids, _option='-l')
                ErrorHandler().waiting(1)
                browser.execute_script("$.Dialog.close()")
                ErrorHandler().printToLog('\n\nBids lowered...\n'
                        , "", logsPath)
                self.startTime = time.time()
                self.adjustBids = 1
                self.campaigns = self.getCampaignStatus()
        elif self.totalCalls > self.maxCallLimit and not self.isPaused:
            self.campaigns = self.getCampaignStatus()
            if not self.isPaused:
                ErrorHandler().switchToTab(self.bidsPageTab)
                browser.execute_script("changeRevPieCampaignStatus(" + campaignID + ", 1)")
                ErrorHandler().printToLog('\n\nCampaign Paused...\n'
                        , "", logsPath)
                self.campaigns = self.getCampaignStatus()
        elif self.totalCalls < 3 and self.isPaused:
            self.campaigns = self.getCampaignStatus()
            if self.isPaused:
                ErrorHandler().switchToTab(self.bidsPageTab)
                browser.execute_script("changeRevPieCampaignStatus(" + campaignID + ", 0)")
                ErrorHandler().printToLog('\n\nCampaign un-paused...\n'
                        , "", logsPath)
                self.campaigns = self.getCampaignStatus()
        elif self.totalCalls < 3 and not self.isPaused and self.adjustBids == 1 :
            _timeDiff = time.time() - self.startTime
            if _timeDiff > (5 * 60):
                ErrorHandler().switchToTab(self.bidsPageTab)
                browser.execute_script("revPieBidAdjustments("
                                        + campaignID + ", '" + campaignName + "')")
                ErrorHandler().waiting(1)
                Bids = BidAdjuster.copyBids()
                ErrorHandler().waiting(1)
                BidAdjuster.changeBids(*Bids)
                ErrorHandler().waiting(1)
                browser.execute_script("$.Dialog.close()")
                ErrorHandler().printToLog('\n\nBids raised...\n'
                        , "", logsPath)
                self.startTime = time.time()
                self.adjustBids = 0

    def getCalls(self):
        ''' Count calls in queue
        '''
        ErrorHandler().switchToTab(self.wallboardTab)
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
            ErrorHandler().printToLog("\n\nBrowser error: wallboard\n"
                        , err, logsPath)
            self.totalCalls = 0
            ErrorHandler().checkBrowser()
            return(self.totalCalls)

    def autoRevPie(self, repsAvail):
        ''' Will run through conditions to monitor - 
            calls on wallboard, reps in queue, and campaign performance.
            Then automatically makes adjustments based on criteria.
            * Must be executed in a loop to run continuously
        '''
        ErrorHandler().checkBrowser()
        # check if repsAvail == None, this will avoid NaN error for callLimit
        if repsAvail is None and self.getReps:
            ErrorHandler().printToLog("\nError: failed to get rep count, using default callLimit=8...\n\n"
                    , "", logsPath)
            self.getReps = False
        elif repsAvail is 0 and self.getReps:
            ErrorHandler().printToLog("\nError: failed to get rep count, using default callLimit=8...\n\n"
                    , "", logsPath)
            self.getReps = False
        elif repsAvail is not None and self.getReps:
            self.adjustBids_CallLimit = round((repsAvail * self.repsToCallsRatio), 0)
            self.getReps = True
        elif repsAvail is not None and self.getReps is False:
            if repsAvail > 0:
                self.getReps = True

        try:
            # update calls
            self.totalCalls = self.getCalls()
            # output
            print('\r' + ' Reps: ' + str(repsAvail)
                  + '  AdjustBids-CallLimit: ', self.adjustBids_CallLimit
                  , '  AutoPause-CallLimit:  ', self.maxCallLimit
                  , '  Total Calls: ', self.totalCalls, ' '
                  , end="", flush = True)
        except Exception as err:
            ErrorHandler().printToLog("\n\nautoPause: Error while printing output\n"
                        , err, logsPath)
            sys.exit(1)

        # 8am - 11am
        if (datetime.datetime.now().time() > datetime.datetime.strptime("08:59", "%H:%M").time()
        and datetime.datetime.now().time() < datetime.datetime.strptime("11:00", "%H:%M").time()
        and datetime.datetime.today().weekday() < 5):
            self.currentCampaign = 0
            if self.campaigns[self.currentCampaign][2]:
                self.isPaused = True
            elif not self.campaigns[self.currentCampaign][2]:
                self.isPaused = False
            if (datetime.datetime.now().time() > datetime.datetime.strptime("08:59", "%H:%M").time()
            and datetime.datetime.now().time() < datetime.datetime.strptime("09:01", "%H:%M").time()
            and datetime.datetime.today().weekday() < 5):
                if self.isPaused:
                    ErrorHandler().switchToTab(self.bidsPageTab)
                    browser.execute_script("changeRevPieCampaignStatus(" + self.campaigns[self.currentCampaign][1] + ", 0)")
                    ErrorHandler().printToLog('\n\n9am-11am Campaign started\n'
                            , "", logsPath)
                    self.campaigns = self.getCampaignStatus()
                    for i in range(60 * 2):
                        if i < (60 * 2):
                            self.watchCalls(self.campaigns[self.currentCampaign][1]
                                            , self.campaigns[self.currentCampaign][0])
                            ErrorHandler().waiting(1)
            self.watchCalls(self.campaigns[self.currentCampaign][1]
                            , self.campaigns[self.currentCampaign][0])
        # 11am - 7pm
        elif (datetime.datetime.now().time() > datetime.datetime.strptime("11:01", "%H:%M").time()
        and datetime.datetime.now().time() < datetime.datetime.strptime("19:00", "%H:%M").time()
        and datetime.datetime.today().weekday() < 5):
            self.currentCampaign = 1
            if self.campaigns[self.currentCampaign][2]:
                self.isPaused = True
            elif not self.campaigns[self.currentCampaign][2]:
                self.isPaused = False
            if (datetime.datetime.now().time() > datetime.datetime.strptime("11:01", "%H:%M").time()
            and datetime.datetime.now().time() < datetime.datetime.strptime("11:02", "%H:%M").time()
            and datetime.datetime.today().weekday() < 5):
                self.switchCampaigns( self.campaigns[self.currentCampaign-1][1]
                                    , self.campaigns[self.currentCampaign-1][0]
                                    , self.campaigns[self.currentCampaign][1]
                                    , self.campaigns[self.currentCampaign][0])
                ErrorHandler().printToLog('\n\nSwitched to 11am campaign...\n'
                        , "", logsPath)
                # wait until 11:02
                for i in range(60):
                    if i < (60):
                        self.watchCalls(self.campaigns[self.currentCampaign][1]
                                        , self.campaigns[self.currentCampaign][0])
                        ErrorHandler().waiting(1)
            self.watchCalls(self.campaigns[self.currentCampaign][1]
                            , self.campaigns[self.currentCampaign][0])
        # 7pm - close
        elif (datetime.datetime.now().time() > datetime.datetime.strptime("19:01", "%H:%M").time()
        and datetime.datetime.now().time() < datetime.datetime.strptime("21:00", "%H:%M").time()
        and datetime.datetime.today().weekday() < 5):
            self.currentCampaign = 2
            if self.campaigns[self.currentCampaign][2]:
                self.isPaused = True
            elif not self.campaigns[self.currentCampaign][2]:
                self.isPaused = False
            if (datetime.datetime.now().time() > datetime.datetime.strptime("19:01", "%H:%M").time()
            and datetime.datetime.now().time() < datetime.datetime.strptime("19:02", "%H:%M").time()
            and datetime.datetime.today().weekday() < 5):
                ErrorHandler().switchToTab(self.bidsPageTab)
                self.switchCampaigns( self.campaigns[self.currentCampaign-1][1]
                                    , self.campaigns[self.currentCampaign-1][0]
                                    , self.campaigns[self.currentCampaign][1]
                                    , self.campaigns[self.currentCampaign][0])
                ErrorHandler().printToLog('\n\nSwitched to 7pm campaign...\n'
                        , "", logsPath)
                # wait until 19:02
                for i in range(60):
                    if i < (60):
                        self.watchCalls(self.campaigns[self.currentCampaign][1]
                                        , self.campaigns[self.currentCampaign][0])
                        ErrorHandler().waiting(1)
            elif (datetime.datetime.now().time() > datetime.datetime.strptime("20:55", "%H:%M").time()
            and datetime.datetime.now().time() < datetime.datetime.strptime("21:01", "%H:%M").time()
            and datetime.datetime.today().weekday() < 5):
                browser.execute_script("changeRevPieCampaignStatus(" + self.campaigns[self.currentCampaign][1] + ", 1)")
                self.campaigns = self.getCampaignStatus()
                ErrorHandler().printToLog('\n\n7pm-close Campaign Paused...\n'
                        , "", logsPath)
                # wait until next day
                if datetime.datetime.today().weekday() == 4:
                    for i in range(60 * 60 * 24 * 2.5):
                        if i < (60 * 60 * 24 * 2.5):
                            ErrorHandler().waiting(1)
                elif datetime.datetime.today().weekday() < 5:
                    for i in range(60 * 60 * 12):
                        if i < (60 * 60 * 12):
                            ErrorHandler().waiting(1)
        return(self.currentCampaign)

# ******************************************************************

    class autoBidAdjust:
        ''' Contains methods to automatically manipulate RevPie bids.\n
            :Methods:
            - copyBids() : Will copy current bids and clicks/min for all sources.
            - changeBids(sourceIDs, clicksPerMin, customBids, _option = None, changeAmount = 0.04, minCPM = 0)
                :Args:
                * sourceIDs, clicksPerMin, customBids :
                    - Each argument takes a list value type.
                    - Call copyBids() to get current values in a tuple
                :Optional Args:
                    * changeAmount=0.4 :
                        - Set custom bid increment with changeAmount=x
                    * minCPM=0
                        - Only SourceIDs with Clicks/Min over the CPM will be changed.
                    * _option=None
                        - By default will raise bids by changeAmount
                    * _option='-l'
                        - Use to decrease by changeAmount instead.
                    * _option='-p'
                        - Use to paste customBids. 
        '''
        def __init__(self):
            self.sourceIDs = []
            self.clicksPerMin = []
            self.customBids = []

        def copyBids(self):
            ''' Will copy current bids and clicks/min for all sources.
                Requires the Bid Adjustments dialog box to be 
                opened and on active page.
                * Returns a tuple of lists: [ self.sourceIDs[0], self.clicksPerMin, self.customBids) ]
            '''
            # wait for the table
            ErrorHandler().waiting(1)
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
            _i = 0
            try:
                for index in range(len(tableValues)):
                    if tableValues[index] == self.sourceIDs[0][_i]:
                        self.clicksPerMin.append(tableValues[index+3])
                        _i += 1
            except:pass
            for index in range(len(self.sourceIDs[0])):
                _customBidID = r"customBid_" + str(self.sourceIDs[0][index])
                try:
                    output = data.find("input", {"id": _customBidID})['value']
                    self.customBids.append(output)
                except:pass
            return( self.sourceIDs[0]
                  , self.clicksPerMin
                  , self.customBids)

        def makeChange(self, __textBox, __newBid, _item):
            ''' changeBids() helper function.\n
                Will make custom bid adjustment (__newBid) to SourceID:_item
                * __textBox is webdriver element
            '''
            __textBox.send_keys(Keys.CONTROL, 'a')
            __textBox.send_keys(str(__newBid))
            ErrorHandler().waiting(1)
            browser.execute_script("makeCustomBidAdjustment('" + str(_item) + "')")

        def changeBids(self, sourceIDs, clicksPerMin, customBids, _option = None, changeAmount = 0.04, minCPM = 0):
            ''' :Args:
                * sourceIDs, clicksPerMin, customBids :
                    - Each argument takes a list value type.
                    - Call copyBids() to get current values in a tuple
                :Optional Args:\n
                * changeAmount=0.4 :
                    - Set custom bid increment with changeAmount=x
                * minCPM=0
                    - Only SourceIDs with Clicks/Min greater than the CPM will be changed.
                * _option=None
                    - By default will raise bids by changeAmount
                * _option='-l'
                    - Use to decrease by changeAmount instead.
                * _option='-p'
                    - Use to paste customBids.
            '''
            if _option == '-p': # change date filter to All if pasting bids
                browser.execute_script("changeBidAdjustmentsDateFilter('all')")
                ErrorHandler().waiting(1)
                _loop = True
                while _loop:
                    if (str(browser.find_element_by_id(
                            'bidAdjustmentsDateFilter').get_attribute(
                                    "value")) == "all"):
                        _loop = False
                    else:
                        ErrorHandler().checkBrowser()
                ErrorHandler().waiting(1)
                WebDriverWait(browser, 15).until(
                        expected_conditions.presence_of_element_located(
                                (By.ID, 'bidAdjustmentsTable')))
            # iterate through sourceIDs
            for index, item in enumerate(sourceIDs):
                _customBidID = r"customBid_" + str(item)
                try:
                    _textBox = browser.find_element_by_id(_customBidID)
                except:pass # will pass if the sourceID is not available
                else:
                    if _option == '-p': # paste bids
                        _newBid = float(customBids[index])
                        self.makeChange(_textBox, _newBid, item)
                    elif _option == '-l': # lower bids
                        # if lowering bids check Clicks/min
                        if float(self.clicksPerMin[index]) > minCPM:
                            _newBid = float(customBids[index]) - changeAmount
                            self.makeChange(_textBox, _newBid, item)
                    elif _option is None: # default will raise bids
                        _newBid = float(customBids[index]) + changeAmount
                        self.makeChange(_textBox, _newBid, item)

# ******************************************************************

    class RepCount:
        ''' Will open QueueOrder page,
            parse table to get repCount,
            and refresh page to get updated count
        '''
        def __init__ (self, _queueOrderTab):
            self.queueOrderTab = _queueOrderTab
            self.repCount = 0

        def getRepsMain(self):
            ''' Will load QueueOrder page in new tab,
                then selects the Rollover queue.
                * Returns the initial repCount as int
            '''
            try:
                browser.execute_script("window.location = '/Maintenance/QueueOrder'")
                ErrorHandler().waiting(1)
                WebDriverWait(browser, 10).until(
                        expected_conditions.presence_of_element_located(
                                (By.XPATH, "//select[@name='queueNumber']/option[text()='Rollover']")))
                browser.find_element_by_xpath(
                        "//select[@name='queueNumber']/option[text()='Rollover']").click()
                browser.find_element_by_name('QueueList').click()
                ErrorHandler().waiting(1)
                self.repCount = self.getRepsTable()
                return(self.repCount)
            except Exception as err:
                ErrorHandler().printToLog("\nBrowser error, failed to get queue order\n"
                        , err, logsPath)
                return(None)

        def getRepsTable(self):
            ''' Will parse the QueueList table,
                and return repCount as int
            '''
            try: # get the table
                WebDriverWait(browser, 15).until(
                        expected_conditions.presence_of_element_located(
                                (By.XPATH, "//table[@class='table striped bordered hovered']")))
                root = lxml.html.fromstring(browser.page_source)
                table =  root.xpath("//table[@class='table striped bordered hovered']")[0]
                # iterate over all the rows   
                for row in table.xpath(".//tr"):
                    # get the text from all the td's from each row
                    repTable = [td.text for td in row.xpath(".//td[text()][last()-2]")]
                self.repCount = list(map(int, repTable))
                return(int(self.repCount[0]))
            except Exception as err:
                ErrorHandler().printToLog("\n\nError: failed to get reps in queue\n"
                        , err, logsPath)
                ErrorHandler().waiting(1)
                return(None)

        def getRepsUpdate(self):
            ''' Method to update repCount value
                after getRepsMain() has been called.
                * Should be called only once every 10 minutes.
            '''
            try:
                # switch to tab for queue order
                ErrorHandler().switchToTab(self.queueOrderTab)
                ErrorHandler().waiting(1)
                browser.refresh()
                ErrorHandler().waiting(1)
                WebDriverWait(browser, 5).until(
                        expected_conditions.alert_is_present())
                alert = browser.switch_to.alert
                alert.accept() # accept form resubmit
            except TimeoutException as err:
                ErrorHandler().printToLog("getRepsUpdate(): timeout exception"
                        , err, logsPath)
            ErrorHandler().waiting(1)
            self.repCount = self.getRepsTable()
            return(self.repCount)

# ******************************************************************

    class RevPieStats:
        ''' Will parse Campaign Performance Report to 
            get performance statistics for sources.
            - metrics: sourceID, clicks, applications, cost, revenue
        '''
        def __init__(self, _revpieStatsTab):
            self.revpieStatsTab = _revpieStatsTab
            self.currentCampaign = 0
            self.sourceIDs = []
            self.clicks = []
            self.appCount = []
            self.cost = []
            self.revenue = []

        def getStatsPage(self, currentCampaign, campaignName):
            ''' Will load Campaign Performance Report for the current campaign
            '''
            try:
                ErrorHandler().switchToTab(self.revpieStatsTab)
                browser.execute_script("window.location = '/Affiliates/RevPieCampaignPerformance'")
                ErrorHandler().waiting(1)
                WebDriverWait(browser, 60).until(
                        expected_conditions.presence_of_element_located(
                                (By.NAME, "CampaignId")))
                self.currentCampaign = currentCampaign
                if self.currentCampaign == 0:
                    browser.find_element_by_xpath(
                            "//select[@name='CampaignId']/option[text()='" + campaignName + "']").click()
                if self.currentCampaign == 1:
                    browser.find_element_by_xpath(
                            "//select[@name='CampaignId']/option[text()='" + campaignName + "']").click()
                if self.currentCampaign == 2:
                    browser.find_element_by_xpath(
                            "//select[@name='CampaignId']/option[text()='" + campaignName + "']").click()
                browser.find_element_by_name('GetReport').click()
            except KeyboardInterrupt as err:
                print("\n", err)
                sys.exit(1)
            except Exception as err:
                ErrorHandler().printToLog("\ngetStatsPage() error: failed to get campaign performance stats\n"
                        , err, logsPath)

        def getStatsTable(self):
            ''' Will read the Campaign Performance Report table 
                and store each metric in a separate array.
                * Returns a tuple of arrays.
            '''
            try:
                WebDriverWait(browser, 30).until(
                        expected_conditions.presence_of_element_located(
                                (By.XPATH, "//table[@class='table striped bordered hovered']")))
                ErrorHandler().waiting(1)
                root = lxml.html.fromstring(browser.page_source)
                table = root.xpath("//table[@class='table striped bordered hovered']")[0]
                # iterate over all the rows
                tableValues = []
                self.clicks = []
                self.appCount = []
                self.cost = []
                self.revenue = []
                for td in table.xpath('.//td'):
                    tableValues.append(td.text)
                self.sourceIDs.append(tableValues[::10])
                _i = 0
                try:
                    for index in range(len(tableValues)):
                        if tableValues[index] == self.sourceIDs[0][_i]:
                            self.clicks.append(tableValues[index+1])
                            self.appCount.append(tableValues[index+2])
                            self.cost.append(tableValues[index+3])
                            self.revenue.append(tableValues[index+4])
                            _i += 1
                except:pass
                return( self.sourceIDs[0]
                      , self.clicks
                      , self.appCount
                      , self.cost
                      , self.revenue )
            except KeyboardInterrupt as err:
                print("\n", err)
                sys.exit(1)
            except Exception as err:
                ErrorHandler().printToLog("\n\ngetStatsTable(): error while loading table, check logs\n"
                        , err, logsPath)
                ErrorHandler().checkBrowser()

        def getStatsUpdate(self, currentCampaign, campaignName):
            ''' Will check if currentCampaign has changed,
                then will call getStatsTable() to get updated values.
                * Returns a tuple of arrays, each metric is a separate array.
            '''
            if currentCampaign != self.currentCampaign:
                self.getStatsPage(currentCampaign, campaignName)
                self.currentCampaign = currentCampaign
                tableValues = self.getStatsTable()
                return(tableValues)
            else:
                ErrorHandler().switchToTab(self.revpieStatsTab)
                try:
                    browser.refresh()
                    ErrorHandler().waiting(1)
                    WebDriverWait(browser, 7).until(
                            expected_conditions.alert_is_present())
                    alert = browser.switch_to.alert
                    alert.accept() # accept form resubmit
                except TimeoutException as err:
                    ErrorHandler().printToLog("\n\ngetRepsUpdate(): timeout exception\n"
                            , err, logsPath)
                tableValues = self.getStatsTable()
                return(tableValues)

# ******************************************************************

class ErrorHandler:
    ''' Handles exceptions and logging.
    '''
    def printToLog(self, message, err, _fpath):
        ''' Will print message to screen, and Exception as err
            with traceback to 'logs.txt'
        '''
        # print message to screen
        print(message)
        if _fpath is None:
            _fpath = self.getLogFile()
        # print error message to file with timestamp and Exception
        _fpath = _fpath
        with open(_fpath, 'a') as f:
            print(datetime.datetime.now(), '\n' + ('-' * 20), message, file=f)
            print(str(err), file=f)
            print(traceback.format_exc(), file=f)

    def getLogFile(self):
        try:
            with open ((Config.config_path+"/config.ini"), 'r') as f:
                    _logsPath=f.readline()
        except:
            _logsPath=Config.config_path+"/error_logs.txt"
        return(_logsPath)

    def waiting(self, duration):
        ''' Will call time.sleep(duration) and handle KeyboardInterrupt exceptions.
        '''
        try:
            time.sleep(duration)
        except KeyboardInterrupt as err:
            self.printToLog("\n"
                        , err, logsPath)
            self.checkBrowser()

    def switchToTab(self, tab):
        ''' Will switch browser tabs by index. \n
            : Arg :  (tab)
            - takes an int type corresponding to the browser tab index
        '''
        try:
            self.waiting(1)
            browser.switch_to.window(browser.window_handles[tab])
        except Exception as err:
            self.printToLog("\n\n\nswitchTabs: Error while switching tabs, closing...\n"
                        , err, logsPath)
        except KeyboardInterrupt as err:
            self.printToLog("\n"
                        , err, logsPath)
            sys.exit(1)

    def checkBrowser(self):
        ''' Will call webdriver.title to check if browser is currently open and responding.
            If not, handles exceptions and exits program.
        '''
        try:
            browser.title
        except Exception as err:
            self.printToLog("\n\ncheckBrowser: Error, closing...\n"
                    , err, logsPath)
            try:
                sys.exit(1)
                return(False)
            except:pass
        else:
            return(True)

# ---END OF CLASS DEFS---
###############################################################################
# FUNCTION DEFS:

def start_browser():
    ''' *
    '''
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
        ErrorHandler().printToLog("\n\nWebDriver: Error on browser setup"
                    , err, logsPath)
        sys.exit(1)

def getLoginInfo(_option):
    ''' - accepted values for _option: '-u' || '-p'
    '''
    if _option == '-u':
        try:
            u = input("\n Input Admin Username: ")
            return(u)
        except KeyboardInterrupt:
            print("\n")
            sys.exit(1)
        except Exception as err:
            ErrorHandler().printToLog("\n\nError during user input, closing...\n"
                        , err, logsPath)
            sys.exit(1)
    elif _option == '-p':
        try:
            p = getpass(prompt="  password: ")
            # admin_pass = input("  password: ")
            print("\n . . . \n")
            return(p)
        except KeyboardInterrupt:
            print("\n")
            sys.exit(1)
        except Exception as err:
            ErrorHandler().printToLog("\n\nError during user input, closing...\n"
                        , err, logsPath)
            sys.exit(1)

def admin_login(_u, _p):
    ''' *
    '''
    try:
        wait = WebDriverWait(browser, 3)
        wait.until(
                expected_conditions.presence_of_element_located(
                        (By.ID, "UserName")))
    except Exception as err:
        ErrorHandler().printToLog("\nBrowser Error: failed to login to admin, closing..."
                , err, logsPath)
        ErrorHandler().checkBrowser()
        sys.exit(1)
    else:
        # type credentials
        text_area = browser.find_element_by_css_selector('#UserName')
        text_area.send_keys(Keys.CONTROL, 'a')
        text_area.send_keys(_u)
        text_area = browser.find_element_by_id('Password')
        text_area.send_keys(Keys.CONTROL, 'a')
        text_area.send_keys(_p)
        # click log in button
        browser.find_element_by_xpath("//input[@type='submit' and @value='Log in']").click()
        WebDriverWait(browser, 3).until(
                expected_conditions.presence_of_element_located(
                        (By.ID, 'formId')))
        # skip seat selection
        browser.execute_script("window.location = '/skipseat1234'")
        ErrorHandler().waiting(1)

def queueDaddy_login(username, password):
    ''' *
    '''
    try:
        wait = WebDriverWait(browser, 15)
        wait.until(
                expected_conditions.presence_of_element_located(
                        (By.XPATH, "//input[@name='userName']")))
    except Exception as err:
        ErrorHandler().printToLog("\nBrowser Error: failed to login to QueueDaddy, closing..."
                , err, logsPath)
        ErrorHandler().checkBrowser()
        sys.exit(1)
    else:
        text_area = browser.find_element_by_xpath("//input[@name='userName']")
        text_area.send_keys(username)
        text_area = browser.find_element_by_xpath("//input[@name='passWord']")
        text_area.send_keys(password)

        browser.find_element_by_xpath("//button[@value='Submit']").click()
        ErrorHandler().waiting(1)

# ---END OF FUNC DEFS---
###############################################################################

with open(Config.getfpath(__file__)+"/AutomateRevPie.info", 'r') as f:
    print("\n####################################################################\n\n")
    print(" . . . ", f.readline())
browser = start_browser()


