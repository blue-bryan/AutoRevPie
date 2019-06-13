#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-Created on Thu Jun 6, 2019
-@author: bryan
"""

class RepCount:
    ''' Will open QueueOrder page,
        parse table to get repCount,
        and refresh page to get updated count
    '''
    def __init__ (self, _queueOrderTab, _Browser, _ErrorHandler):
        self.Browser = _Browser
        self.ErrorHandler = _ErrorHandler
        self.queueOrderTab = _queueOrderTab
        self.repCount = 0

    def getRepsMain(self):
        ''' Will load QueueOrder page in new tab,
            then selects the Rollover queue.
            * Returns the initial repCount as int
        '''
        try:
            self.Browser.browser.execute_script("window.location = '/Maintenance/QueueOrder'")
            self.ErrorHandler.waiting(1)
            self.Browser.WebDriverWait(self.Browser.browser, 10).until(
                    self.Browser.expected_conditions.presence_of_element_located(
                            (self.Browser.By.XPATH, "//select[@name='queueNumber']/option[text()='Rollover']")))
            self.Browser.browser.find_element_by_xpath(
                    "//select[@name='queueNumber']/option[text()='Rollover']").click()
            self.Browser.browser.find_element_by_name('QueueList').click()
            self.ErrorHandler.waiting(1)
            self.repCount = self.getRepsTable()
            return(self.repCount)
        except Exception as err:
            self.ErrorHandler.printToLog("\nBrowser error, failed to get queue order\n"
                    , err, self.ErrorHandler.getLogFile())
            return(None)

    def getRepsTable(self):
        ''' Will parse the QueueList table,
            and return repCount as int
        '''
        try: # get the table
            self.Browser.WebDriverWait(self.Browser.browser, 15).until(
                    self.Browser.expected_conditions.presence_of_element_located(
                            (self.Browser.By.XPATH, "//table[@class='table striped bordered hovered']")))
            root = self.Browser.lxml.html.fromstring(self.Browser.browser.page_source)
            table =  root.xpath("//table[@class='table striped bordered hovered']")[0]
            # iterate over all the rows   
            for row in table.xpath(".//tr"):
                # get the text from all the td's from each row
                repTable = [td.text for td in row.xpath(".//td[text()][last()-2]")]
            self.repCount = list(map(int, repTable))
            return(int(self.repCount[0]))
        except Exception as err:
            self.ErrorHandler.printToLog("\n\nError: failed to get reps in queue\n"
                    , err, self.ErrorHandler.getLogFile())
            self.ErrorHandler.waiting(1)
            return(None)

    def getRepsUpdate(self):
        ''' Method to update repCount value
            after getRepsMain() has been called.
            * Should be called only once every 10 minutes.
        '''
        try:
            # switch to tab for queue order
            self.Browser.BrowserHandler().switchToTab(self.queueOrderTab)
            self.ErrorHandler.waiting(1)
            self.Browser.browser.refresh()
            self.ErrorHandler.waiting(1)
            self.Browser.WebDriverWait(self.Browser.browser, 5).until(
                    self.Browser.expected_conditions.alert_is_present())
            alert = self.Browser.browser.switch_to.alert
            alert.accept() # accept form resubmit
        except self.Browser.TimeoutException as err:
            self.ErrorHandler.printToLog("getRepsUpdate(): timeout exception"
                    , err, self.ErrorHandler.getLogFile())
        self.ErrorHandler.waiting(1)
        self.repCount = self.getRepsTable()
        return(self.repCount)

# ---END OF CLASS DEF---
####################################################################
