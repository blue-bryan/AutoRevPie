#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-Created on Wed May  8 09:41:43 2019
-@author: bryan

-A modular library using Selenium WebDriver built to fully automate
 traffic monitoring and the bidding process for RevPie.
"""

from AutomateRevPie import ARP_WebDriver as Browser
from AutomateRevPie.ARP_WebDriver import BrowserHandler
from AutomateRevPie.ARP_WebDriver import EH

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
        self.isPaused = True
        self.adjustBids_CallLimit  = 8 # default callLimit == 8
        self.repsToCallsRatio = 0.25 # ratio to use for callLimit...
                                     # x% of Reps in Queue = callLimit
        self.maxCallLimit = 10 # limit of number of calls before pausing campaign
        self.adjustBids = 0
        self.totalCalls = 0
        self.currentCampaign = 0
        self.campaigns = [ # [name, ID, status]
                           ["RP101_8am_to_11am", "390", True] 
                         , ["RP_102_11am to 7pm", "396", True]
                         , ["RP_103_7pmClose", "391", True]
                         , ["Closed", "0", True] ]

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
            EH.Handler().waiting(2)
            Browser.browser.execute_script("$('#RevPieCampaigns').click()")
            wait.until(
                    Browser.expected_conditions.presence_of_element_located(
                            (Browser.By.ID, "revPieCampaignsDiv")))
        except Exception as err:
            EH.Handler().printToLog("\n\nBrowser Error: failed to open Bid Adjustments, closing...\n"
                        , err, EH.Handler().getLogFile())
            BrowserHandler().checkBrowser()

    def getCampaignStatus(self):
        ''' Will iterate the RevPie Campaigns table and get
            the pause status of each campaign in the campaigns[] array,
            then returns the array.
            * paused==True/active==False
        '''
        BrowserHandler().switchToTab(self.bidsPageTab)
        try:
            Browser.WebDriverWait(Browser.browser, 15).until(
                    Browser.expected_conditions.presence_of_element_located(
                            (Browser.By.ID, "revPieCampaignsDiv")))
        except Exception as err:
            EH.Handler().printToLog("\n\nBrowser Error while getting campaign status, closing...\n"
                        , err, EH.Handler().getLogFile())
            BrowserHandler().checkBrowser()
            return(False)
        else:
            Browser.browser.execute_script("$('#RevPieCampaigns').click()")
            try:
                EH.Handler().waiting(1)
                _loop = True
                while _loop:
                    if (str(Browser.browser.find_element_by_id(
                            'ajax-loading').get_attribute(
                                    "style")) == "display: none;"):
                        _loop = False
                    else:
                        BrowserHandler().checkBrowser()
            except Exception as err:
                EH.Handler().printToLog("\n\ngetCampaignStatus: error, cannot find 'revPieCampaignsDiv'\n"
                        , err, EH.Handler().getLogFile())
                return(False)
            else:
                # get the table
                table =  Browser.browser.find_element_by_xpath(
                        "//table[@class='table striped nbm bordered hovered']")
                tableValues = []
                for i in table.find_elements_by_tag_name('span'):
                    tableValues.append(i.text) 
                # iterate over all the rows
                for _index, _item in enumerate(tableValues):
                    if _item == "RP101_8am_to_11am":
                        if tableValues[_index+2] == "paused":
                            self.campaigns[0][2] = True
                        else:
                            self.campaigns[0][2] = False
                    elif _item == "RP_102_11am to 7pm":
                        if tableValues[_index+2] == "paused":
                            self.campaigns[1][2] = True
                        else:
                            self.campaigns[1][2] = False
                    elif _item == "RP_103_7pmClose":
                        if tableValues[_index+2] == "paused":
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
        self.isPaused = self.campaigns[self.currentCampaign][2]
        if self.totalCalls > self.adjustBids_CallLimit and not self.isPaused and self.adjustBids == 0:
            if not self.isPaused:
                BrowserHandler().switchToTab(self.bidsPageTab)
                EH.Handler().waiting(1)
                Browser.browser.execute_script("revPieBidAdjustments("
                                        + campaignID + ", '" + campaignName + "')")
                EH.Handler().waiting(2)
                Bids = BidAdjuster.copyBids()
                EH.Handler().waiting(1)
                BidAdjuster.changeBids(*Bids, _option='-l')
                EH.Handler().waiting(1)
                Browser.browser.execute_script("$.Dialog.close()")
                EH.Handler().printToLog('\n\nBids lowered...\n'
                        , "", EH.Handler().getLogFile())
                self.startTime = EH.Config.time.time()
                self.adjustBids = 1
                self.campaigns = self.getCampaignStatus()
        elif self.totalCalls > self.maxCallLimit and not self.isPaused:
            _timeDiff = EH.Config.time.time() - self.startTime
            if _timeDiff > (60):
                self.campaigns = self.getCampaignStatus()
                if not self.isPaused:
                    BrowserHandler().switchToTab(self.bidsPageTab)
                    Browser.browser.execute_script("changeRevPieCampaignStatus(" + campaignID + ", 1)")
                    EH.Handler().printToLog('\n\nCampaign Paused...\n'
                            , "", EH.Handler().getLogFile())
                    self.campaigns = self.getCampaignStatus()
                    self.startTime = EH.Config.time.time()
        elif self.totalCalls < 3 and self.isPaused:
            self.campaigns = self.getCampaignStatus()
            if self.isPaused:
                BrowserHandler().switchToTab(self.bidsPageTab)
                Browser.browser.execute_script("changeRevPieCampaignStatus(" + campaignID + ", 0)")
                EH.Handler().printToLog('\n\nCampaign un-paused...\n'
                        , "", EH.Handler().getLogFile())
                self.campaigns = self.getCampaignStatus()
        elif self.totalCalls < 3 and not self.isPaused and self.adjustBids == 1:
            _timeDiff = EH.Config.time.time() - self.startTime
            if _timeDiff > (5 * 60):
                BrowserHandler().switchToTab(self.bidsPageTab)
                Browser.browser.execute_script("revPieBidAdjustments("
                                        + campaignID + ", '" + campaignName + "')")
                EH.Handler().waiting(1)
                Bids = BidAdjuster.copyBids()
                EH.Handler().waiting(1)
                BidAdjuster.changeBids(*Bids)
                EH.Handler().waiting(1)
                Browser.browser.execute_script("$.Dialog.close()")
                EH.Handler().printToLog('\n\nBids raised...\n'
                        , "", EH.Handler().getLogFile())
                self.startTime = EH.Config.time.time()
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
        BrowserHandler().switchToTab(self.bidsPageTab)
        Browser.browser.execute_script("changeRevPieCampaignStatus(" + campaignID_1 + ", 1)")
        EH.Handler().waiting(1)
        Browser.browser.execute_script("changeRevPieCampaignStatus(" + campaignID_2 + ", 0)")
        EH.Handler().waiting(2)
        Browser.browser.execute_script("revPieBidAdjustments("
                                + campaignID_1 + ", '" + campaignName_1 + "')")
        EH.Handler().waiting(1)
        Browser.WebDriverWait(Browser.browser, 15).until(
                Browser.expected_conditions.presence_of_element_located(
                        (Browser.By.ID,'bidAdjustmentsTable')))
        EH.Handler().waiting(1)
        Bids = BidAdjuster.copyBids()
        EH.Handler().waiting(1)
        Browser.browser.execute_script("$.Dialog.close()")
        EH.Handler().waiting(2)
        Browser.browser.execute_script("revPieBidAdjustments("
                                + campaignID_2 + ", '" + campaignName_2 + "')")
        EH.Handler().waiting(2)
        BidAdjuster.changeBids(*Bids, _option='-p')
        EH.Handler().waiting(2)
        Browser.browser.execute_script("$.Dialog.close()")

    def getCalls(self):
        ''' Count calls in queue
        '''
        BrowserHandler().switchToTab(self.wallboardTab)
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
            EH.Handler().printToLog("\n\nBrowser error: wallboard\n"
                        , err, EH.Handler().getLogFile())
            self.totalCalls = 0
            BrowserHandler().checkBrowser()
            return(self.totalCalls)

    def autoRevPie(self, repsAvail):
        ''' Will run through conditions to monitor - 
            calls on wallboard, reps in queue, and campaign performance.
            Then automatically makes adjustments based on criteria.
            * Must be executed in a loop to run continuously
        '''
        BrowserHandler().checkBrowser()
        # check if repsAvail == None, this will avoid NaN error for callLimit
        if self.getReps:
            if repsAvail is None or repsAvail == 0:
                EH.Handler().printToLog("\nError: failed to get rep count, using default callLimit : 8...\n\n"
                        , "", EH.Handler().getLogFile())
                self.getReps = False
            else:
                self.adjustBids_CallLimit = round((repsAvail * self.repsToCallsRatio), 0)
                self.getReps = True
        elif repsAvail is not None and not self.getReps:
            if repsAvail > 0:
                self.getReps = True

        try:
            # update calls
            self.totalCalls = self.getCalls()
            # output
            print('\r' + ' isPaused: ' + str(self.isPaused)
                  + '  Reps: ' + str(repsAvail)
                  + '  AdjustBids-CallLimit: ', self.adjustBids_CallLimit
                  , '  AutoPause-CallLimit:  ', self.maxCallLimit
                  , '  Total Calls: ', self.totalCalls, ' '
                  , end="", flush = True)
        except Exception as err:
            EH.Handler().printToLog("\n\nautoPause: Error while printing output\n"
                        , err, EH.Handler().getLogFile())
            EH.Config.sys.exit(1)

        # 8am - 11am
        if (EH.Config.datetime.datetime.now().time() > EH.Config.datetime.datetime.strptime("08:59", "%H:%M").time()
        and EH.Config.datetime.datetime.now().time() < EH.Config.datetime.datetime.strptime("11:00", "%H:%M").time()
        and EH.Config.datetime.datetime.today().weekday() < 5):
            self.currentCampaign = 0
            self.isPaused = self.campaigns[self.currentCampaign][2]
            if (EH.Config.datetime.datetime.now().time() > EH.Config.datetime.datetime.strptime("08:59", "%H:%M").time()
            and EH.Config.datetime.datetime.now().time() < EH.Config.datetime.datetime.strptime("09:01", "%H:%M").time()
            and EH.Config.datetime.datetime.today().weekday() < 5):
                if self.isPaused:
                    BrowserHandler().switchToTab(self.bidsPageTab)
                    Browser.browser.execute_script("changeRevPieCampaignStatus(" + self.campaigns[self.currentCampaign][1] + ", 0)")
                    EH.Handler().printToLog('\n\n9am-11am Campaign started\n'
                            , "", EH.Handler().getLogFile())
                    self.campaigns = self.getCampaignStatus()
                    for i in range(60 * 2):
                        if i < (60 * 2):
                            self.watchCalls(self.campaigns[self.currentCampaign][1]
                                            , self.campaigns[self.currentCampaign][0])
                            EH.Handler().waiting(1)
            self.watchCalls(self.campaigns[self.currentCampaign][1]
                            , self.campaigns[self.currentCampaign][0])
        # 11am - 7pm
        elif (EH.Config.datetime.datetime.now().time() > EH.Config.datetime.datetime.strptime("11:01", "%H:%M").time()
        and EH.Config.datetime.datetime.now().time() < EH.Config.datetime.datetime.strptime("19:00", "%H:%M").time()
        and EH.Config.datetime.datetime.today().weekday() < 5):
            self.currentCampaign = 1
            self.isPaused = self.campaigns[self.currentCampaign][2]
            if (EH.Config.datetime.datetime.now().time() > EH.Config.datetime.datetime.strptime("11:01", "%H:%M").time()
            and EH.Config.datetime.datetime.now().time() < EH.Config.datetime.datetime.strptime("11:02", "%H:%M").time()
            and EH.Config.datetime.datetime.today().weekday() < 5):
                self.switchCampaigns( self.campaigns[self.currentCampaign-1][1]
                                    , self.campaigns[self.currentCampaign-1][0]
                                    , self.campaigns[self.currentCampaign][1]
                                    , self.campaigns[self.currentCampaign][0] )
                EH.Handler().printToLog('\n\nSwitched to 11am campaign...\n'
                        , "", EH.Handler().getLogFile())
                # wait until 11:02
                for i in range(60):
                    if i < (60):
                        self.watchCalls(self.campaigns[self.currentCampaign][1]
                                        , self.campaigns[self.currentCampaign][0])
                        EH.Handler().waiting(1)
            self.watchCalls(self.campaigns[self.currentCampaign][1]
                            , self.campaigns[self.currentCampaign][0])
        # 7pm - close
        elif (EH.Config.datetime.datetime.now().time() > EH.Config.datetime.datetime.strptime("19:01", "%H:%M").time()
        and EH.Config.datetime.datetime.now().time() < EH.Config.datetime.datetime.strptime("21:00", "%H:%M").time()
        and EH.Config.datetime.datetime.today().weekday() < 5):
            self.currentCampaign = 2
            self.isPaused = self.campaigns[self.currentCampaign][2]
            if (EH.Config.datetime.datetime.now().time() > EH.Config.datetime.datetime.strptime("19:01", "%H:%M").time()
            and EH.Config.datetime.datetime.now().time() < EH.Config.datetime.datetime.strptime("19:02", "%H:%M").time()
            and EH.Config.datetime.datetime.today().weekday() < 5):
                BrowserHandler().switchToTab(self.bidsPageTab)
                self.switchCampaigns( self.campaigns[self.currentCampaign-1][1]
                                    , self.campaigns[self.currentCampaign-1][0]
                                    , self.campaigns[self.currentCampaign][1]
                                    , self.campaigns[self.currentCampaign][0] )
                EH.Handler().printToLog('\n\nSwitched to 7pm campaign...\n'
                        , "", EH.Handler().getLogFile())
                # wait until 19:02
                for i in range(60):
                    if i < (60):
                        self.watchCalls(self.campaigns[self.currentCampaign][1]
                                        , self.campaigns[self.currentCampaign][0])
                        EH.Handler().waiting(1)
            elif (EH.Config.datetime.datetime.now().time() > EH.Config.datetime.datetime.strptime("20:55", "%H:%M").time()
            and EH.Config.datetime.datetime.now().time() < EH.Config.datetime.datetime.strptime("21:01", "%H:%M").time()
            and EH.Config.datetime.datetime.today().weekday() < 5):
                Browser.browser.execute_script("changeRevPieCampaignStatus(" + self.campaigns[self.currentCampaign][1] + ", 1)")
                self.campaigns = self.getCampaignStatus()
                EH.Handler().printToLog('\n\n7pm-close Campaign Paused...\n'
                        , "", EH.Handler().getLogFile())
                # wait until next day
                if EH.Config.datetime.datetime.today().weekday() == 4:
                    for i in range(60 * 60 * 24 * 2.5):
                        if i < (60 * 60 * 24 * 2.5):
                            EH.Handler().waiting(1)
                elif EH.Config.datetime.datetime.today().weekday() < 5:
                    for i in range(60 * 60 * 12):
                        if i < (60 * 60 * 12):
                            EH.Handler().waiting(1)
        else:
            self.currentCampaign = 3
            self.isPaused = self.campaigns[self.currentCampaign][2]
        return(self.currentCampaign, self.isPaused)

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
        self.prevCPM = []
        self.clicksPerMin = []
        self.customBids = []

    def copyBids(self):
        ''' Will copy current bids and clicks/min for all sources.
            Requires the Bid Adjustments dialog box to be 
            opened and on active page.
            * Returns a tuple of lists: [ self.sourceIDs[0], self.clicksPerMin, self.customBids) ]
        '''
        # wait for the table...
        EH.Handler().waiting(1)
        Browser.WebDriverWait(Browser.browser, 15).until(
                Browser.expected_conditions.presence_of_element_located(
                        (Browser.By.ID,'bidAdjustmentsTable')))
        # get the table...
        data = Browser.bs4.BeautifulSoup(Browser.browser.page_source, "lxml")
        root = Browser.lxml.html.fromstring(Browser.browser.page_source)
        table = root.xpath("//table[@class='table striped nbm bordered']")[0]
        # iterate over all the rows...
        tableValues = []
        self.sourceIDs = []
        self.clicksPerMin = []
        self.customBids = []
        for td in table.xpath('.//td'):
            tableValues.append(td.text)
        # Source IDs...
        self.sourceIDs.append(tableValues[::7])
        # Clicks/Min...
        _i = 0
        for _index, _item in enumerate(tableValues):
            if _i <= len(self.sourceIDs[0]):
                try:
                    if int(_item) == int(self.sourceIDs[0][_i]):
                        if tableValues[_index+3] is not None:
                            self.clicksPerMin.append(float(tableValues[_index+3]))
                        elif tableValues[_index+3] is None:
                            self.clicksPerMin.append(0)
                        _i += 1
                except:pass
        if max(self.clicksPerMin) > 0:
            self.prevCPM = self.clicksPerMin
        if max(self.clicksPerMin) == 0:
            self.clicksPerMin = self.prevCPM
        # Custom Bids...
        for _index in range(len(self.sourceIDs[0])):
            _customBidID = r"customBid_" + str(self.sourceIDs[0][_index])
            try:
                output = data.find("input", {"id": _customBidID})['value']
                self.customBids.append(float(output))
            except:pass
        print( self.sourceIDs[0]
                , self.clicksPerMin
                , self.customBids )
        return( self.sourceIDs[0]
                , self.clicksPerMin
                , self.customBids )

    def makeChange(self, __textBox, __newBid, _sourceID):
        ''' changeBids() helper function.\n
            Will make custom bid adjustment (__newBid) to _sourceID
            * __textBox is webdriver element
        '''
        __textBox.send_keys(Browser.Keys.CONTROL, 'a')
        __textBox.send_keys(str(__newBid))
        EH.Handler().waiting(1)
        Browser.browser.execute_script("makeCustomBidAdjustment('" + str(_sourceID) + "')")

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
            EH.Handler().waiting(2)
            _loop = True
            while _loop:
                if (str(Browser.browser.find_element_by_id(
                        'ajax-loading').get_attribute(
                                "style")) == "display: none;"):
                    _loop = False
                else:
                    BrowserHandler().checkBrowser()
            EH.Handler().waiting(2)
            Browser.WebDriverWait(Browser.browser, 15).until(
                    Browser.expected_conditions.presence_of_element_located(
                            (Browser.By.ID, 'bidAdjustmentsTable')))
        # iterate through sourceIDs
        for _index, _item in enumerate(sourceIDs):
            _elementID = r"customBid_" + str(_item)
            try:
                _textBox = Browser.browser.find_element_by_id(_elementID)
            except:pass # will pass if the sourceID is not available
            finally:
                if _option is None: # default will raise bids
                    _newBid = customBids[_index] + changeAmount
                    self.makeChange(_textBox, _newBid, sourceIDs[_index])
                elif _option == '-p': # paste bids
                    _newBid = customBids[_index]
                    self.makeChange(_textBox, _newBid, sourceIDs[_index])
        if _option == '-l': # lower bids
            # if lowering bids check Clicks/min
            _index = clicksPerMin.index(max(clicksPerMin))
            _elementID = r"customBid_" + str(sourceIDs[_index])
            _textBox = Browser.browser.find_element_by_id(_elementID)
            _newBid = customBids[_index] - changeAmount
            self.makeChange(_textBox, _newBid, sourceIDs[_index])

# ******************************************************************
# ---END OF CLASS DEFS---
####################################################################

# print version info
with open(EH.Config.getfpath(__file__)+"/AutomateRevPie.info", 'r') as f:
    print("\n####################################################################\n\n")
    print(" . . . ", f.readline())


