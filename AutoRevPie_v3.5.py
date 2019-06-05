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
import lxml.html
import traceback
import configparser
from getpass import getpass
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.common.exceptions import TimeoutException

###############################################################################
# CLASS DEF: AutoRevPie

class AutoRevPie:
    ''' Contains methods and functions
        to automatically monitor and adjust RevPie Campaigns.
        for further info read doc file '''

    def __init__ (self):
        self.getReps = True
        self.isPaused = False
        self.adjustBids = 0
        self.totalCalls = 0
        self.callLimit = 10 # default callLimit == 8
        self.repsToCalls = 0.25 # ratio to use for callLimit...
                                # x% of Reps in Queue = callLimit
        self.pauseThreshold = 11
        self.currentCampaign = None
        self.campaigns = [ ["RP101_8am_to_11am", "390", False]   # [name, ID, status]
                         , ["RP_102_11am to 7pm", "396", False]
                         , ["RP_103_7pmClose", "391", False] ]

    def openBidAdjustments(self):
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

    def printIsPaused(self):
        if self.isPaused:
            print('\nCampaign is currently: Paused\n\n')
            return(self.isPaused)
        else:
            print('\nCampaign is currently: Active\n')
            return(self.isPaused)

    def getCampaignStatus(self):
        ''' Will iterate the RevPie Campaigns table and get
            the pause status of each campaign in the campaigns[] array,
            then returns the array.
            * paused==True/active==False'''

        switchToTab(bidsPageTab)
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
            browser.execute_script("$('#RevPieCampaigns').click()")
            try:
                WebDriverWait(browser, 15).until(
                        expected_conditions.presence_of_element_located(
                                (By.ID, "revPieCampaignsDiv")))
            except Exception as err:
                printToLog("\n\ngetCampaignStatus: error, cannot find 'revPieCampaignsDiv'\n"
                        , err)
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

    def switchCampaigns(self, campaignID_1, campaignID_2, campaignName_1, campaignName_2):
        BidAdjuster = AutoRevPie.autoBidAdjust()
        switchToTab(bidsPageTab)
        browser.execute_script("changeRevPieCampaignStatus(" + campaignID_1 + ", 1)")
        waiting(1)
        browser.execute_script("changeRevPieCampaignStatus(" + campaignID_2 + ", 0)")
        waiting(2)
        browser.execute_script("revPieBidAdjustments("
                                + campaignID_1 + ", '" + campaignName_1 + "')")
        waiting(1)
        WebDriverWait(browser, 15).until(
                expected_conditions.presence_of_element_located(
                        (By.ID,'bidAdjustmentsTable')))
        waiting(1)
        BidAdjuster.copyBids()
        waiting(1)
        browser.execute_script("$.Dialog.close()")
        waiting(2)
        browser.execute_script("revPieBidAdjustments("
                                + campaignID_2 + ", '" + campaignName_2 + "')")
        waiting(5)
        BidAdjuster.pasteBids()
        waiting(1)
        browser.execute_script("$.Dialog.close()")

    def watchCalls(self, campaignID, campaignName):
        ''' Will make adjustments to RevPie campaign status
            and bids based on criteria.
            * Used in AutoRevPie() so current campaign
              can be assigned based on time conditions '''

        BidAdjuster = AutoRevPie.autoBidAdjust()
        if self.totalCalls > self.callLimit and not self.isPaused and self.adjustBids == 0:
            if not self.isPaused:
                switchToTab(bidsPageTab)
                waiting(1)
                browser.execute_script("revPieBidAdjustments("
                                        + campaignID + ", '" + campaignName + "')")
                waiting(2)
                BidAdjuster.copyBids()
                waiting(1)
                BidAdjuster.lowerBids()
                waiting(1)
                browser.execute_script("$.Dialog.close()")
                printToLog('\n\nBids lowered...\n', "")
                self.startTime = time.time()
                self.adjustBids = 1
                self.campaigns = self.getCampaignStatus()
        elif self.totalCalls > self.pauseThreshold and not self.isPaused:
            self.campaigns = self.getCampaignStatus()
            if not self.isPaused:
                switchToTab(bidsPageTab)
                browser.execute_script("changeRevPieCampaignStatus(" + campaignID + ", 1)")
                printToLog('\n\nCampaign Paused...\n', "")
                self.campaigns = self.getCampaignStatus()
        elif self.totalCalls < 3 and not self.isPaused and self.adjustBids == 1 :
            _timeDiff = time.time() - self.startTime
            if _timeDiff > (5 * 60):
                switchToTab(bidsPageTab)
                browser.execute_script("revPieBidAdjustments("
                                        + campaignID + ", '" + campaignName + "')")
                waiting(1)
                browser.execute_script("revPieBidAdjustments("
                                        + campaignID + ", '" + campaignName + "')")
                waiting(2)
                BidAdjuster.raiseBids()
                waiting(1)
                browser.execute_script("$.Dialog.close()")
                printToLog('\n\nBids raised...\n', "")
                _startTime = time.time()
                self.adjustBids = 0
        elif self.totalCalls < 3 and self.isPaused:
            self.campaigns = self.getCampaignStatus()
            if self.isPaused:
                switchToTab(bidsPageTab)
                browser.execute_script("changeRevPieCampaignStatus(" + campaignID + ", 0)")
                printToLog('\n\nCampaign un-paused...\n', "")
                self.campaigns = self.getCampaignStatus()

    # Count calls in queue
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

    def AutoRevPie(self, repsAvail):
        ''' Will run through conditions to monitor - 
            calls on wallboard, reps in queue, and campaign performance.
            Then automatically makes adjustments based on criteria.
            * Must be executed in a loop to run continuously '''

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

        # 8am - 11am
        if (datetime.datetime.now().time() > datetime.datetime.strptime("08:59", "%H:%M").time()
        and datetime.datetime.now().time() < datetime.datetime.strptime("11:00", "%H:%M").time()
        and datetime.datetime.today().weekday() < 5):
            self.currentCampaign = 0
            if self.campaigns[self.currentCampaign][2]:
                self.isPaused = True
            elif self.campaigns[self.currentCampaign][2]:
                self.isPaused = False
            if (datetime.datetime.now().time() > datetime.datetime.strptime("08:59", "%H:%M").time()
            and datetime.datetime.now().time() < datetime.datetime.strptime("09:01", "%H:%M").time()
            and datetime.datetime.today().weekday() < 5):
                if self.isPaused:
                    switchToTab(bidsPageTab)
                    browser.execute_script("changeRevPieCampaignStatus(" + self.campaigns[self.currentCampaign][1] + ", 0)")
                    printToLog('\n\n9am-11am Campaign started\n', "")
                    self.campaigns = self.getCampaignStatus()
                    for i in range(60 * 2):
                        if i < (60 * 2):
                            self.watchCalls(self.campaigns[self.currentCampaign][1]
                                            , self.campaigns[self.currentCampaign][0])
                            waiting(1)
            self.watchCalls(self.campaigns[self.currentCampaign][1]
                            , self.campaigns[self.currentCampaign][0])
        # 11am - 7pm
        elif (datetime.datetime.now().time() > datetime.datetime.strptime("11:01", "%H:%M").time()
        and datetime.datetime.now().time() < datetime.datetime.strptime("19:00", "%H:%M").time()
        and datetime.datetime.today().weekday() < 5):
            self.currentCampaign = 1
            if self.campaigns[self.currentCampaign][2]:
                self.isPaused = True
            elif self.campaigns[self.currentCampaign][2]:
                self.isPaused = False
            if (datetime.datetime.now().time() > datetime.datetime.strptime("11:01", "%H:%M").time()
            and datetime.datetime.now().time() < datetime.datetime.strptime("11:02", "%H:%M").time()
            and datetime.datetime.today().weekday() < 5):
                self.switchCampaigns(self.campaigns[(self.currentCampaign-1)][1]
                                    , self.campaigns[(self.currentCampaign-1)][1]
                                    , self.campaigns[self.currentCampaign][0]
                                    , self.campaigns[self.currentCampaign][0])
                printToLog('\n\nSwitched to 11am campaign...\n', "")
                # wait until 11:02
                for i in range(60):
                    if i < (60):
                        self.watchCalls(self.campaigns[self.currentCampaign][1]
                                        , self.campaigns[self.currentCampaign][0])
                        waiting(1)
            self.watchCalls(self.campaigns[self.currentCampaign][1]
                            , self.campaigns[self.currentCampaign][0])
        # 7pm - close
        elif (datetime.datetime.now().time() > datetime.datetime.strptime("19:01", "%H:%M").time()
        and datetime.datetime.now().time() < datetime.datetime.strptime("21:00", "%H:%M").time()
        and datetime.datetime.today().weekday() < 5):
            self.currentCampaign = 2
            if self.campaigns[self.currentCampaign][2]:
                self.isPaused = True
            elif self.campaigns[self.currentCampaign][2]:
                self.isPaused = False
            if (datetime.datetime.now().time() > datetime.datetime.strptime("19:01", "%H:%M").time()
            and datetime.datetime.now().time() < datetime.datetime.strptime("19:02", "%H:%M").time()
            and datetime.datetime.today().weekday() < 5):
                switchToTab(bidsPageTab)
                self.switchCampaigns(self.campaigns[(self.currentCampaign-1)][1]
                                    , self.campaigns[(self.currentCampaign-1)][1]
                                    , self.campaigns[self.currentCampaign][0]
                                    , self.campaigns[self.currentCampaign][0])
                printToLog('\n\nSwitched to 7pm campaign...\n', "")
                # wait until 19:02
                for i in range(60):
                    if i < (60):
                        self.watchCalls(self.campaigns[self.currentCampaign][1]
                                        , self.campaigns[self.currentCampaign][0])
                        waiting(1)
            elif (datetime.datetime.now().time() > datetime.datetime.strptime("20:55", "%H:%M").time()
            and datetime.datetime.now().time() < datetime.datetime.strptime("21:01", "%H:%M").time()
            and datetime.datetime.today().weekday() < 5):
                browser.execute_script("changeRevPieCampaignStatus(" + self.campaigns[self.currentCampaign][1] + ", 1)")
                self.campaigns = self.getCampaignStatus()
                printToLog('\n\n7pm-close Campaign Paused...\n', "")
                # wait until next day
                if datetime.datetime.today().weekday() == 4:
                    for i in range(60 * 60 * 24 * 2.5):
                        if i < (60 * 60 * 24 * 2.5):
                            waiting(1)
                elif datetime.datetime.today().weekday() < 5:
                    for i in range(60 * 60 * 12):
                        if i < (60 * 60 * 12):
                            waiting(1)

# ******************************************************************

    class autoBidAdjust:
        ''' Contains methods to automatically manipulate
            RevPie bids '''

        def __init__(self):
            self.sourceIDs = []
            self.customBids = []

        def copyBids(self):
            ''' Will copy current bids for all sources.
                Requires the Bid Adjustments dialog box to be 
                opened and on active page. '''

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
            print(customBids)
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
            try:
                sourceIDs = self.sourceIDs[0]
                customBids = self.customBids
            except:pass # silent fail if no previous values stored, i.e copyBids() was not called
            for index, item in enumerate(sourceIDs):
                _customBidID = r"customBid_" + str(item)
                WebDriverWait(browser, 15).until(
                        expected_conditions.presence_of_element_located(
                                (By.ID, 'bidAdjustmentsTable')))
                try:
                    text_area = browser.find_element_by_id(_customBidID)
                    text_area.send_keys(Keys.CONTROL, 'a')
                    waiting(1)
                    _newBid = float(customBids[index]) - 0.04
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
                        _newBid = float(customBids[index]) + 0.06
                        text_area.send_keys(str(_newBid))
                        waiting(1)
                        browser.execute_script("makeCustomBidAdjustment('" + str(item) + "')")
                    except:pass # will pass if the sourceID is not available

# ******************************************************************

    class RepCount:
        ''' Will open QueueOrder page,
            parse table to get repCount,
            and refresh page to get updated count '''

        def __init__ (self):
            self.repCount = 0

        def getRepsMain(self):
            ''' Will load QueueOrder page in new tab,
                then selects the Rollover queue.
                * Returns the initial repCount as int '''

            try:
                browser.execute_script("window.location = '/Maintenance/QueueOrder'")
                waiting(1)
                browser.find_element_by_xpath(
                        "//select[@name='queueNumber']/option[text()='Rollover']").click()
                browser.find_element_by_name('QueueList').click()
                waiting(1)
                self.repCount = self.getRepsTable()
                return(self.repCount)
            except Exception as err:
                printToLog("\nBrowser error, failed to get queue order\n"
                        , err)
                return(None)

        def getRepsTable(self):
            ''' Will parse the QueueList table,
                and return repCount as int '''

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
                printToLog("\n\nError: failed to get reps in queue\n"
                        , err)
                waiting(1)
                return(None)

        def getRepsUpdate(self):
            ''' Function call to update repCount value
                after getRepsMain() has been called.
                * Should be executed only once every 10 minutes. '''

            try:
                # switch to tab for queue order
                switchToTab(queueOrderTab)
                waiting(1)
                browser.refresh()
                waiting(1)
                WebDriverWait(browser, 5).until(
                        expected_conditions.alert_is_present())
                alert = browser.switch_to.alert
                alert.accept() # accept form resubmit
            except TimeoutException as err:
                printToLog("getRepsUpdate(): timeout exception"
                        , err)
            waiting(1)
            self.repCount = self.getRepsTable()
            return(self.repCount)

# ******************************************************************

    class RevPieStats:
        ''' Will parse Campaign Performance Report to 
            get performance statistics for sources.
            - metrics: sourceID, clicks, applications, cost, revenue '''

        def __init__(self):
            self.currentCampaign = None
            self.sourceIDs = []
            self.clicks = []

        def getStatsPage(self, currentCampaign, campaignName):
            ''' Will load Campaign Performance Report for the current campaign
                * Requires tab with Campaign Performance Report to be open '''

            try:
                switchToTab(revpieStatsTab)
                waiting(1)
                WebDriverWait(browser, 30).until(
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
                printToLog("\ngetStatsPage() error: failed to get campaign performance stats\n"
                        , err)

        def getStatsTable(self):
            ''' Will read the Campaign Performance Report table 
                and store each metric in a separate array.
                * Returns a tuple of arrays. '''

            try:
                WebDriverWait(browser, 30).until(
                        expected_conditions.presence_of_element_located(
                                (By.XPATH, "//table[@class='table striped bordered hovered']")))
                waiting(1)
                root = lxml.html.fromstring(browser.page_source)
                table = root.xpath("//table[@class='table striped bordered hovered']")[0]
                # iterate over all the rows
                tableValues = []
                for td in table.xpath('.//td'):
                    tableValues.append(td.text)
                self.sourceIDs.append(tableValues[::10])
                _i = 0
                try:
                    for index in range(len(tableValues)):
                        if tableValues[index] == self.sourceIDs[0][_i]:
                            self.clicks.append(tableValues[index+1])
                            _i += 1
                except:pass
                return(self.sourceIDs[0], self.clicks)
            except KeyboardInterrupt as err:
                print("\n", err)
                sys.exit(1)
            except Exception as err:
                printToLog("\n\ngetStatsTable(): error while loading table, check logs\n"
                        , err)
                checkBrowser()

        def getStatsUpdate(self, currentCampaign, campaignID):
            ''' Will check if currentCampaign has changed,
                then will call getStatsTable() to get updated values.
                * Returns a tuple of arrays, each metric is a separate array. '''

            if currentCampaign != self.currentCampaign:
                self.getStatsPage(currentCampaign, campaignID)
                self.currentCampaign = currentCampaign
            else:
                switchToTab(revpieStatsTab)
                try:
                    browser.refresh()
                    waiting(1)
                    WebDriverWait(browser, 7).until(
                            expected_conditions.alert_is_present())
                    alert = browser.switch_to.alert
                    alert.accept() # accept form resubmit
                except TimeoutException as err:
                    printToLog("\n\ngetRepsUpdate(): timeout exception\n"
                            , err)
                tableValues = self.getStatsTable()
                return(tableValues)

# ---END OF CLASS DEF---
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

def getLoginInfo(_option):
    if _option == "-u":
        try:
            u = input("\n Input Admin Username: ")
            return(u)
        except KeyboardInterrupt:
            print("\n")
            sys.exit(1)
        except Exception as err:
            printToLog("\n\nError during user input, closing...\n"
                        , err)
            sys.exit(1)
    elif _option == "-p":
        try:
            p = getpass(prompt="  password: ")
            # admin_pass = input("  password: ")
            print("\n . . . \n")
            return(p)
        except KeyboardInterrupt:
            print("\n")
            sys.exit(1)
        except Exception as err:
            printToLog("\n\nError during user input, closing...\n"
                        , err)
            sys.exit(1)

def admin_login(_u, _p):
    try:
        wait = WebDriverWait(browser, 3)
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

def waiting(duration):
    try:
        time.sleep(duration)
    except KeyboardInterrupt as err:
        printToLog("\n"
                    , err)
        checkBrowser()

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
        sys.exit(1)

def getFilename(filename):
    ''' Will return a full file path, with the current working directory
         using the given filename. '''

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
    ''' Will open (or create a file if none exists),
        named 'logs.txt' in the working directory. '''

    filename = getFilename("logs.txt")
    # open log file and print header to file
    with open(filename, 'w') as f:
        print('Filename:', filename, file=f)
        print('\n\n - - - Logs (' + str(time.strftime("%Y-%m-%d %H:%M.%S")) + ')' + ' - - - ' + '\n', file=f)

def printToLog(message, err):
    ''' Will print message to screen, and Exception as err
        with traceback to 'logs.txt' '''

    # print message to screen
    print(message)
    # print error message to file with timestamp and Exception
    filename = getFilename("logs.txt")
    with open(filename, 'a') as f:
        print(datetime.datetime.now(), '\n' + ('-' * 20), message, file=f)
        print(str(err), file=f)
        print(traceback.format_exc(), file=f)

# ---END OF FUNC DEFS---
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
    printToLog("\n\nopenLog: Error while loading '/log.txt', logs will not be recorded\n"
                , err)
    sys.exit(1)

################################ CONFIG #######################################
# CONFIG FILE SHOULD BE IN THE WORKING DIRECTORY

# get config file
try:
    # open file
    configParser = configparser.RawConfigParser()
    configParser.read_file(open(getFilename("config.txt")))
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

# save tabs to variables to be used with switchTabs()
wallboardTab = 0
queueOrderTab = 1
revpieStatsTab = 2
bidsPageTab = 3

AutoRP = AutoRevPie()
RepCounter = AutoRevPie.RepCount()
CampaignStats = AutoRevPie.RevPieStats()
try:
    # load wallboard
    browser.get(wallboard)
    waiting(1)
    queueDaddy_login(queue_uname, queue_pass)
    waiting(1)
    # load admin page
    browser.execute_script("window.open('" + admin + "')")
    # login to admin
    waiting(1)
    switchToTab(queueOrderTab)
    login = True
    while login:
        try:
            admin_login(getLoginInfo("-u"), getLoginInfo("-p"))
        except KeyboardInterrupt:
            print("\n")
            sys.exit(1)
        except Exception as err:
            printToLog("\nError: Incorrect Username/Password, try again\n"
                        , err)
            print("\n . . . \n")
        else:
            login = False
    # get initial rep count
    repsAvail = RepCounter.getRepsMain()
    # load campaign performance page
    browser.execute_script("window.open('" + admin + "/Affiliates/RevPieCampaignPerformance')")
    switchToTab(revpieStatsTab)
    # load reporting page for bid adjustments
    waiting(1)
    browser.execute_script("window.open('" + admin + "')")
    switchToTab(bidsPageTab)
    AutoRP.openBidAdjustments()
    waiting(1)
    AutoRP.printIsPaused()
except KeyboardInterrupt:
    print("\n")
    sys.exit(1)
except Exception as err:
    printToLog("\n\nError while loading tabs, closing...\n"
                , err)
    sys.exit(1)

############################### - MAIN - ######################################

loop = True
while loop:
    loop = checkBrowser()
    try:
        AutoRP.AutoRevPie(RepCounter.repCount)
    except KeyboardInterrupt:
        print("\n")
        sys.exit(1)
    except Exception as err:
        printToLog("\n\nError: error while executing AutoRevPie, closing...\n"
                    , err)
        browser.quit()
        sys.exit(1)
    # update revpieStats on every 5th minute of the hour...
    if datetime.datetime.now().minute % 5 == 0:
        _startTime = datetime.datetime.now().minute
        # also update queue order if 10th minute of the hour...
        if datetime.datetime.now().minute % 10 == 0:
            try:
                waiting(1)
                RepCounter.repCount = RepCounter.getRepsUpdate()
                waiting(1)
                CampaignStats.getStatsPage(AutoRP.currentCampaign
                                            , AutoRP.campaigns[AutoRP.currentCampaign][0])
                print(CampaignStats.getStatsUpdate(AutoRP.currentCampaign
                                                    , AutoRP.campaigns[AutoRP.currentCampaign][0]), '\n')
                _wait = True
                while _wait:
                    if datetime.datetime.now().minute == (_startTime + 1):
                        _wait = False
                    waiting(1)
                    AutoRP.AutoRevPie(RepCounter.repCount)
            except KeyboardInterrupt:
                print("\n")
                sys.exit(1)
            except Exception as err:
                printToLog("\n\nError: unable to update rep count..."
                , err)
        else: # else just get revpieStats
            try:
                CampaignStats.getStatsPage(AutoRP.currentCampaign
                                            , AutoRP.campaigns[AutoRP.currentCampaign][0])
                print(CampaignStats.getStatsUpdate(AutoRP.currentCampaign
                                                    , AutoRP.campaigns[AutoRP.currentCampaign][0]), '\n')
                waiting(1)
                _wait = True
                while _wait:
                    if datetime.datetime.now().minute == (_startTime + 1):
                        _wait = False
                    waiting(1)
                    AutoRP.AutoRevPie(RepCounter.repCount)
            except KeyboardInterrupt:
                print("\n")
                sys.exit(1)
            except Exception as err:
                printToLog("\n\nError: unable to update revpieStats..."
                , err)


