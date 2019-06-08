#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-Created on Wed May  8 09:41:43 2019
-@author: bryan

-A modular library using Selenium WebDriver built to fully automate
 traffic monitoring and the bidding process for RevPie.
"""

import time
import datetime
import lxml.html
from bs4 import BeautifulSoup

import AutomateRevPie.ARP_WebDriver as Browser

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
            wait = Browser.WebDriverWait(Browser.browser, 30)
            Browser.browser.get(self.admin + "/Maintenance")
            wait.until(
                    Browser.expected_conditions.presence_of_element_located(
                            (Browser.By.XPATH, "//a[.='RevPie Reporting']")))
            accordionFrame = Browser.browser.find_element_by_xpath("//a[.='RevPie Reporting']")
            actions = Browser.ActionChains(Browser.browser)
            actions.move_to_element(accordionFrame).click().perform()
            Browser.ErrorHandler().waiting(2)
            Browser.browser.execute_script("$('#RevPieCampaigns').click()")
            wait.until(
                    Browser.expected_conditions.presence_of_element_located(
                            (Browser.By.ID, "revPieCampaignsDiv")))
        except Exception as err:
            Browser.ErrorHandler().printToLog("\n\nBrowser Error: failed to open Bid Adjustments, closing...\n"
                        , err, Browser.ErrorHandler().getLogFile())
            Browser.ErrorHandler().checkBrowser()

    def getCampaignStatus(self):
        ''' Will iterate the RevPie Campaigns table and get
            the pause status of each campaign in the campaigns[] array,
            then returns the array.
            * paused==True/active==False
        '''
        Browser.ErrorHandler().switchToTab(self.bidsPageTab)
        try:
            Browser.WebDriverWait(Browser.browser, 15).until(
                    Browser.expected_conditions.presence_of_element_located(
                            (Browser.By.ID, "revPieCampaignsDiv")))
        except Exception as err:
            Browser.ErrorHandler().printToLog("\n\nBrowser Error while getting campaign status, closing...\n"
                        , err, Browser.ErrorHandler().getLogFile())
            Browser.ErrorHandler().checkBrowser()
            return(False)
        else:
            Browser.browser.execute_script("$('#RevPieCampaigns').click()")
            try:
                Browser.WebDriverWait(Browser.browser, 15).until(
                        Browser.expected_conditions.presence_of_element_located(
                                (Browser.By.ID, "revPieCampaignsDiv")))
            except Exception as err:
                Browser.ErrorHandler().printToLog("\n\ngetCampaignStatus: error, cannot find 'revPieCampaignsDiv'\n"
                        , err, Browser.ErrorHandler().getLogFile())
                return(False)
            else:
                # get the table
                table =  Browser.browser.find_element_by_xpath(
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

    def watchCalls(self, campaignID, campaignName):
        ''' Will make adjustments to RevPie campaign status
            and bids based on criteria.
            * Used in AutoRevPie() so current campaign
              can be assigned based on time conditions
        '''
        BidAdjuster = AutoBidAdjust()
        if self.campaigns[self.currentCampaign][2]:
            self.isPaused = True
        elif not self.campaigns[self.currentCampaign][2]:
            self.isPaused = False
        if self.totalCalls > self.adjustBids_CallLimit and not self.isPaused and self.adjustBids == 0:
            if not self.isPaused:
                Browser.ErrorHandler().switchToTab(self.bidsPageTab)
                Browser.ErrorHandler().waiting(1)
                Browser.browser.execute_script("revPieBidAdjustments("
                                        + campaignID + ", '" + campaignName + "')")
                Browser.ErrorHandler().waiting(2)
                Bids = BidAdjuster.copyBids()
                Browser.ErrorHandler().waiting(1)
                BidAdjuster.changeBids(*Bids, _option='-l')
                Browser.ErrorHandler().waiting(1)
                Browser.browser.execute_script("$.Dialog.close()")
                Browser.ErrorHandler().printToLog('\n\nBids lowered...\n'
                        , "", Browser.ErrorHandler().getLogFile())
                self.startTime = time.time()
                self.adjustBids = 1
                self.campaigns = self.getCampaignStatus()
        elif self.totalCalls > self.maxCallLimit and not self.isPaused:
            self.campaigns = self.getCampaignStatus()
            if not self.isPaused:
                Browser.ErrorHandler().switchToTab(self.bidsPageTab)
                Browser.browser.execute_script("changeRevPieCampaignStatus(" + campaignID + ", 1)")
                Browser.ErrorHandler().printToLog('\n\nCampaign Paused...\n'
                        , "", Browser.ErrorHandler().getLogFile())
                self.campaigns = self.getCampaignStatus()
        elif self.totalCalls < 3 and self.isPaused:
            self.campaigns = self.getCampaignStatus()
            if self.isPaused:
                Browser.ErrorHandler().switchToTab(self.bidsPageTab)
                Browser.browser.execute_script("changeRevPieCampaignStatus(" + campaignID + ", 0)")
                Browser.ErrorHandler().printToLog('\n\nCampaign un-paused...\n'
                        , "", Browser.ErrorHandler().getLogFile())
                self.campaigns = self.getCampaignStatus()
        elif self.totalCalls < 3 and not self.isPaused and self.adjustBids == 1 :
            _timeDiff = time.time() - self.startTime
            if _timeDiff > (5 * 60):
                Browser.ErrorHandler().switchToTab(self.bidsPageTab)
                Browser.browser.execute_script("revPieBidAdjustments("
                                        + campaignID + ", '" + campaignName + "')")
                Browser.ErrorHandler().waiting(1)
                Bids = BidAdjuster.copyBids()
                Browser.ErrorHandler().waiting(1)
                BidAdjuster.changeBids(*Bids)
                Browser.ErrorHandler().waiting(1)
                Browser.browser.execute_script("$.Dialog.close()")
                Browser.ErrorHandler().printToLog('\n\nBids raised...\n'
                        , "", Browser.ErrorHandler().getLogFile())
                self.startTime = time.time()
                self.adjustBids = 0

    def switchCampaigns(self, campaignID_1, campaignName_1, campaignID_2, campaignName_2):
        ''' -
            * usage:\n 
                AutoRevPie.switchCampaigns(AutoRevPie.campaigns[AutoRevPie.currentCampaign-1][1]
                                        , AutoRevPie.campaigns[AutoRevPie.currentCampaign-1][0]
                                        , AutoRevPie.campaigns[AutoRevPie.currentCampaign][1]
                                        , AutoRevPie.campaigns[AutoRevPie.currentCampaign][0])
        '''
        BidAdjuster = AutoBidAdjust()
        Browser.ErrorHandler().switchToTab(self.bidsPageTab)
        Browser.browser.execute_script("changeRevPieCampaignStatus(" + campaignID_1 + ", 1)")
        Browser.ErrorHandler().waiting(1)
        Browser.browser.execute_script("changeRevPieCampaignStatus(" + campaignID_2 + ", 0)")
        Browser.ErrorHandler().waiting(2)
        Browser.browser.execute_script("revPieBidAdjustments("
                                + campaignID_1 + ", '" + campaignName_1 + "')")
        Browser.ErrorHandler().waiting(1)
        Browser.WebDriverWait(Browser.browser, 15).until(
                Browser.expected_conditions.presence_of_element_located(
                        (Browser.By.ID,'bidAdjustmentsTable')))
        Browser.ErrorHandler().waiting(1)
        Bids = BidAdjuster.copyBids()
        Browser.ErrorHandler().waiting(1)
        Browser.browser.execute_script("$.Dialog.close()")
        Browser.ErrorHandler().waiting(2)
        Browser.browser.execute_script("revPieBidAdjustments("
                                + campaignID_2 + ", '" + campaignName_2 + "')")
        Browser.ErrorHandler().waiting(2)
        BidAdjuster.changeBids(*Bids, _option='-p')
        Browser.ErrorHandler().waiting(2)
        Browser.browser.execute_script("$.Dialog.close()")

    def getCalls(self):
        ''' Count calls in queue
        '''
        Browser.ErrorHandler().switchToTab(self.wallboardTab)
        try: # switch to wall board for total calls
            Browser.WebDriverWait(Browser.browser, 15).until(
                    Browser.expected_conditions.presence_of_element_located(
                            (Browser.By.CLASS_NAME, 'container')))
            rollover = Browser.browser.find_element_by_id('queue_count10')
            seniorLoan1 = Browser.browser.find_element_by_id('queue_count16')
            seniorLoan2 = Browser.browser.find_element_by_id('queue_count25')
            # custServ = browser.find_element_by_id('queue_count2')
            self.totalCalls = (int(rollover.text)
                            + int(seniorLoan1.text)
                            + int(seniorLoan2.text))
            return(self.totalCalls)
        except Exception as err:
            Browser.ErrorHandler().printToLog("\n\nBrowser error: wallboard\n"
                        , err, Browser.ErrorHandler().getLogFile())
            self.totalCalls = 0
            Browser.ErrorHandler().checkBrowser()
            return(self.totalCalls)

    def autoRevPie(self, repsAvail):
        ''' Will run through conditions to monitor - 
            calls on wallboard, reps in queue, and campaign performance.
            Then automatically makes adjustments based on criteria.
            * Must be executed in a loop to run continuously
        '''
        Browser.ErrorHandler().checkBrowser()
        # check if repsAvail == None, this will avoid NaN error for callLimit
        if repsAvail is None and self.getReps:
            Browser.ErrorHandler().printToLog("\nError: failed to get rep count, using default callLimit=8...\n\n"
                    , "", Browser.ErrorHandler().getLogFile())
            self.getReps = False
        elif repsAvail is 0 and self.getReps:
            Browser.ErrorHandler().printToLog("\nError: failed to get rep count, using default callLimit=8...\n\n"
                    , "", Browser.ErrorHandler().getLogFile())
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
            Browser.ErrorHandler().printToLog("\n\nautoPause: Error while printing output\n"
                        , err, Browser.ErrorHandler().getLogFile())
            Browser.sys.exit(1)

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
                    Browser.ErrorHandler().switchToTab(self.bidsPageTab)
                    Browser.browser.execute_script("changeRevPieCampaignStatus(" + self.campaigns[self.currentCampaign][1] + ", 0)")
                    Browser.ErrorHandler().printToLog('\n\n9am-11am Campaign started\n'
                            , "", Browser.ErrorHandler().getLogFile())
                    self.campaigns = self.getCampaignStatus()
                    for i in range(60 * 2):
                        if i < (60 * 2):
                            self.watchCalls(self.campaigns[self.currentCampaign][1]
                                            , self.campaigns[self.currentCampaign][0])
                            Browser.ErrorHandler().waiting(1)
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
                Browser.ErrorHandler().printToLog('\n\nSwitched to 11am campaign...\n'
                        , "", Browser.ErrorHandler().getLogFile())
                # wait until 11:02
                for i in range(60):
                    if i < (60):
                        self.watchCalls(self.campaigns[self.currentCampaign][1]
                                        , self.campaigns[self.currentCampaign][0])
                        Browser.ErrorHandler().waiting(1)
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
                Browser.ErrorHandler().switchToTab(self.bidsPageTab)
                self.switchCampaigns( self.campaigns[self.currentCampaign-1][1]
                                    , self.campaigns[self.currentCampaign-1][0]
                                    , self.campaigns[self.currentCampaign][1]
                                    , self.campaigns[self.currentCampaign][0])
                Browser.ErrorHandler().printToLog('\n\nSwitched to 7pm campaign...\n'
                        , "", Browser.ErrorHandler().getLogFile())
                # wait until 19:02
                for i in range(60):
                    if i < (60):
                        self.watchCalls(self.campaigns[self.currentCampaign][1]
                                        , self.campaigns[self.currentCampaign][0])
                        Browser.ErrorHandler().waiting(1)
            elif (datetime.datetime.now().time() > datetime.datetime.strptime("20:55", "%H:%M").time()
            and datetime.datetime.now().time() < datetime.datetime.strptime("21:01", "%H:%M").time()
            and datetime.datetime.today().weekday() < 5):
                Browser.browser.execute_script("changeRevPieCampaignStatus(" + self.campaigns[self.currentCampaign][1] + ", 1)")
                self.campaigns = self.getCampaignStatus()
                Browser.ErrorHandler().printToLog('\n\n7pm-close Campaign Paused...\n'
                        , "", Browser.ErrorHandler().getLogFile())
                # wait until next day
                if datetime.datetime.today().weekday() == 4:
                    for i in range(60 * 60 * 24 * 2.5):
                        if i < (60 * 60 * 24 * 2.5):
                            Browser.ErrorHandler().waiting(1)
                elif datetime.datetime.today().weekday() < 5:
                    for i in range(60 * 60 * 12):
                        if i < (60 * 60 * 12):
                            Browser.ErrorHandler().waiting(1)
        return(self.currentCampaign)

# ******************************************************************

class AutoBidAdjust:
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
        Browser.ErrorHandler().waiting(1)
        Browser.WebDriverWait(Browser.browser, 15).until(
                Browser.expected_conditions.presence_of_element_located(
                        (Browser.By.ID,'bidAdjustmentsTable')))
        # get the table
        data = BeautifulSoup(Browser.browser.page_source, "lxml")
        root = lxml.html.fromstring(Browser.browser.page_source)
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
                , self.customBids )

    def makeChange(self, __textBox, __newBid, _item):
        ''' changeBids() helper function.\n
            Will make custom bid adjustment (__newBid) to SourceID:_item
            * __textBox is webdriver element
        '''
        __textBox.send_keys(Browser.Keys.CONTROL, 'a')
        __textBox.send_keys(str(__newBid))
        Browser.ErrorHandler().waiting(1)
        Browser.browser.execute_script("makeCustomBidAdjustment('" + str(_item) + "')")

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
            Browser.browser.execute_script("changeBidAdjustmentsDateFilter('all')")
            Browser.ErrorHandler().waiting(2)
            _loop = True
            while _loop:
                if (str(Browser.browser.find_element_by_id(
                        'bidAdjustmentsDateFilter').get_attribute(
                                "value")) == "all"):
                    _loop = False
                else:
                    Browser.ErrorHandler().checkBrowser()
            Browser.ErrorHandler().waiting(2)
            Browser.WebDriverWait(Browser.browser, 15).until(
                    Browser.expected_conditions.presence_of_element_located(
                            (Browser.By.ID, 'bidAdjustmentsTable')))
        # iterate through sourceIDs
        for index, item in enumerate(sourceIDs):
            _customBidID = r"customBid_" + str(item)
            try:
                _textBox = Browser.browser.find_element_by_id(_customBidID)
            except:pass # will pass if the sourceID is not available
            else:
                if _option == '-p': # paste bids
                    _newBid = float(customBids[index])
                    self.makeChange(_textBox, _newBid, item)
                elif _option == '-l': # lower bids
                    # if lowering bids check Clicks/min
                    if self.clicksPerMin[index] is not None:
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
            Browser.browser.execute_script("window.location = '/Maintenance/QueueOrder'")
            Browser.ErrorHandler().waiting(1)
            Browser.WebDriverWait(Browser.browser, 10).until(
                    Browser.expected_conditions.presence_of_element_located(
                            (Browser.By.XPATH, "//select[@name='queueNumber']/option[text()='Rollover']")))
            Browser.browser.find_element_by_xpath(
                    "//select[@name='queueNumber']/option[text()='Rollover']").click()
            Browser.browser.find_element_by_name('QueueList').click()
            Browser.ErrorHandler().waiting(1)
            self.repCount = self.getRepsTable()
            return(self.repCount)
        except Exception as err:
            Browser.ErrorHandler().printToLog("\nBrowser error, failed to get queue order\n"
                    , err, Browser.ErrorHandler().getLogFile())
            return(None)

    def getRepsTable(self):
        ''' Will parse the QueueList table,
            and return repCount as int
        '''
        try: # get the table
            Browser.WebDriverWait(Browser.browser, 15).until(
                    Browser.expected_conditions.presence_of_element_located(
                            (Browser.By.XPATH, "//table[@class='table striped bordered hovered']")))
            root = lxml.html.fromstring(Browser.browser.page_source)
            table =  root.xpath("//table[@class='table striped bordered hovered']")[0]
            # iterate over all the rows   
            for row in table.xpath(".//tr"):
                # get the text from all the td's from each row
                repTable = [td.text for td in row.xpath(".//td[text()][last()-2]")]
            self.repCount = list(map(int, repTable))
            return(int(self.repCount[0]))
        except Exception as err:
            Browser.ErrorHandler().printToLog("\n\nError: failed to get reps in queue\n"
                    , err, Browser.ErrorHandler().getLogFile())
            Browser.ErrorHandler().waiting(1)
            return(None)

    def getRepsUpdate(self):
        ''' Method to update repCount value
            after getRepsMain() has been called.
            * Should be called only once every 10 minutes.
        '''
        try:
            # switch to tab for queue order
            Browser.ErrorHandler().switchToTab(self.queueOrderTab)
            Browser.ErrorHandler().waiting(1)
            Browser.browser.refresh()
            Browser.ErrorHandler().waiting(1)
            Browser.WebDriverWait(Browser.browser, 5).until(
                    Browser.expected_conditions.alert_is_present())
            alert = Browser.browser.switch_to.alert
            alert.accept() # accept form resubmit
        except Browser.TimeoutException as err:
            Browser.ErrorHandler().printToLog("getRepsUpdate(): timeout exception"
                    , err, Browser.ErrorHandler().getLogFile())
        Browser.ErrorHandler().waiting(1)
        self.repCount = self.getRepsTable()
        return(self.repCount)

# ******************************************************************

# ******************************************************************
# ---END OF CLASS DEFS---
####################################################################

with open(Browser.Config.getfpath(__file__)+"/AutomateRevPie.info", 'r') as f:
    print("\n####################################################################\n\n")
    print(" . . . ", f.readline())


