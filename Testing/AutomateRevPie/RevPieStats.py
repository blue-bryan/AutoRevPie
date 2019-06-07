#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-Created on Thu Jun 6, 2019
-@author: bryan
"""

import csv

class RevPieStats:
    ''' Will parse Campaign Performance Report to 
        get performance statistics for sources.
        - metrics: sourceID, clicks, applications, cost, revenue
    '''
    def __init__(self, _revpieStatsTab, _Browser):
        self.Browser = _Browser
        self.revpieStatsTab = _revpieStatsTab
        self.currentCampaign = 0
        self.tableHeaders = []
        self.sourceIDs = []
        self.clicks = []
        self.appCount = []
        self.cost = []
        self.revenue = []

    def getStatsPage(self, currentCampaign, campaignName):
        ''' Will load Campaign Performance Report for the current campaign
        '''
        try:
            self.Browser.ErrorHandler().switchToTab(self.revpieStatsTab)
            self.Browser.browser.execute_script("window.location = '/Affiliates/RevPieCampaignPerformance'")
            self.Browser.ErrorHandler().waiting(1)
            self.Browser.WebDriverWait(self.Browser.browser, 60).until(
                    self.Browser.expected_conditions.presence_of_element_located(
                            (self.Browser.By.NAME, "CampaignId")))
            self.currentCampaign = currentCampaign
            if self.currentCampaign == 0:
                self.Browser.browser.find_element_by_xpath(
                        "//select[@name='CampaignId']/option[text()='" + campaignName + "']").click()
            if self.currentCampaign == 1:
                self.Browser.browser.find_element_by_xpath(
                        "//select[@name='CampaignId']/option[text()='" + campaignName + "']").click()
            if self.currentCampaign == 2:
                self.Browser.browser.find_element_by_xpath(
                        "//select[@name='CampaignId']/option[text()='" + campaignName + "']").click()
            self.Browser.browser.find_element_by_name('GetReport').click()
        except KeyboardInterrupt as err:
            print("\n", err)
            self.Browser.sys.exit(1)
        except Exception as err:
            self.Browser.ErrorHandler().printToLog("\ngetStatsPage() error: failed to get campaign performance stats\n"
                    , err, self.Browser.ErrorHandler().getLogFile())

    def getStatsTable(self):
        ''' Will read the Campaign Performance Report table 
            and store each metric in a separate array.
            * Returns a tuple of arrays.
        '''
        try:
            self.Browser.WebDriverWait(self.Browser.browser, 30).until(
                    self.Browser.expected_conditions.presence_of_element_located(
                            (self.Browser.By.XPATH, "//table[@class='table striped bordered hovered']")))
            self.Browser.ErrorHandler().waiting(1)
            root = self.Browser.Config.lxml.html.fromstring(self.Browser.browser.page_source)
            table = root.xpath("//table[@class='table striped bordered hovered']")[0]
            # iterate over all the rows
            tableValues = []
            self.clicks = []
            self.appCount = []
            self.cost = []
            self.revenue = []
            for td in table.xpath('.//td'):
                tableValues.append(td.text)
            self.tableHeaders.append(tableValues[:10])
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
            return( self.tableHeaders
                    , self.sourceIDs[0]
                    , self.clicks
                    , self.appCount
                    , self.cost
                    , self.revenue )
        except KeyboardInterrupt as err:
            print("\n", err)
            self.Browser.sys.exit(1)
        except Exception as err:
            self.Browser.ErrorHandler().printToLog("\n\ngetStatsTable(): error while loading table, check logs\n"
                    , err, self.Browser.ErrorHandler().getLogFile())
            self.Browser.ErrorHandler().checkBrowser()

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
            self.Browser.ErrorHandler().switchToTab(self.revpieStatsTab)
            try:
                self.Browser.browser.refresh()
                self.Browser.ErrorHandler().waiting(1)
                self.Browser.WebDriverWait(self.Browser.browser, 7).until(
                        self.Browser.expected_conditions.alert_is_present())
                alert = self.Browser.browser.switch_to.alert
                alert.accept() # accept form resubmit
            except self.Browser.TimeoutException as err:
                self.Browser.ErrorHandler().printToLog("\n\ngetRepsUpdate(): timeout exception\n"
                        , err, self.Browser.ErrorHandler().getLogFile())
            tableValues = self.getStatsTable()
            return(tableValues)

    def output_stats(self, _mode = None):
        ''' Will output campaign stats to file.
        '''
        _f = self.Browser.Config.getfpath(__file__) + 'rp_stats(' + self.Browser.Config.time.strftime("%Y.%m.%d") + ').csv'
        _existingFile = self.Browser.Config.os.path.isfile(_f)
        if not _existingFile: # write header to file is does not exist already
            _mode =  "-headers"
        with open(_f,'a') as _csvfile:
            csvWriter = csv.writer(_csvfile, delimiter=",")
            if _mode == "-headers":
                csvWriter.writerow(self.tableHeaders)
            csvWriter.writerow(zip( [ self.sourceIDs[0]
                                    , self.clicks
                                    , self.appCount
                                    , self.cost
                                    , self.revenue ] ))
