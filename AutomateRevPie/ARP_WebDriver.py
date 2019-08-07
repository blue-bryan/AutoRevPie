#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-Created on Thu Jun  6 21:22:43 2019
-@author: bryan
"""

from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException

import getpass

import lxml.html
import bs4

import AutomateRevPie.ErrorHandler as EH

class BrowserHandler:
    def start_browser(self):
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
            EH.Handler().printToLog("\n\nWebDriver: Error on browser setup"
                        , err, EH.Handler().getLogFile())
            EH.Config.sys.exit(1)

    def getLoginInfo(self, _option):
        ''' - accepted values for _option: '-u' || '-p'
        '''
        if _option == '-u':
            try:
                u = input("\n Username: ")
                return(u)
            except KeyboardInterrupt:
                print("\n")
                EH.Config.sys.exit(1)
            except Exception as err:
                EH.Handler().printToLog("\n\nError during user input, closing...\n"
                            , err, EH.Handler().getLogFile())
                EH.Config.sys.exit(1)
        elif _option == '-p':
            try:
                p = getpass.getpass(prompt="  password: ")
                # admin_pass = input("  password: ")
                print("\n . . . \n")
                return(p)
            except KeyboardInterrupt:
                print("\n")
                EH.Config.sys.exit(1)
            except Exception as err:
                EH.Handler().printToLog("\n\nError during user input, closing...\n"
                            , err, EH.Handler().getLogFile())
                EH.Config.sys.exit(1)

    def admin_login(self, _u, _p):
        ''' *
        '''
        try:
            wait = WebDriverWait(browser, 3)
            wait.until(
                    expected_conditions.presence_of_element_located(
                            (By.ID, "UserName")))
        except Exception as err:
            EH.Handler().printToLog("\nBrowser Error: failed to login to admin, closing..."
                    , err, EH.Handler().getLogFile())
            self.checkBrowser()
            EH.Config.sys.exit(1)
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
            EH.Handler().waiting(1)

    def queueDaddy_login(self, _u, _p):
        ''' *
        '''
        try:
            wait = WebDriverWait(browser, 3)
            wait.until(
                    expected_conditions.presence_of_element_located(
                            (By.NAME, "userName")))
        except Exception as err:
            EH.Handler().printToLog("\nBrowser Error: failed to login to QueueDaddy, closing..."
                    , err, EH.Handler().getLogFile())
            self.checkBrowser()
            EH.Config.sys.exit(1)
        else:
            text_area = browser.find_element_by_xpath("//input[@name='userName']")
            text_area.send_keys(Keys.CONTROL, 'a')
            text_area.send_keys(_u)
            text_area = browser.find_element_by_xpath("//input[@name='passWord']")
            text_area.send_keys(Keys.CONTROL, 'a')
            text_area.send_keys(_p)

            browser.find_element_by_xpath("//button[@value='Submit']").click()
            EH.Handler().waiting(1)

    def switchToTab(self, tab):
        ''' Will switch self.Browser.browser tabs by index. \n
            : Arg :  (tab)
            - takes an int type corresponding to the self.Browser.browser tab index
        '''
        try:
            EH.Handler().waiting(1)
            browser.switch_to.window(browser.window_handles[tab])
        except Exception as err:
            EH.Handler().printToLog("\n\n\nswitchTabs: Error while switching tabs, closing...\n"
                        , err, EH.Handler().getLogFile())
        except KeyboardInterrupt as err:
            EH.Handler().printToLog("\n"
                        , err, EH.Handler().getLogFile())
            EH.Config.sys.exit(1)

    def checkBrowser(self):
        ''' Will call webdriver.title to check if self.Browser.browser is currently open and responding.
            If not, handles exceptions and exits program.
        '''
        try:
            browser.title
        except Exception as err:
            EH.Handler().printToLog("\n\ncheckBrowser: Error, closing...\n"
                    , err, EH.Handler().getLogFile())
            try:
                browser.quit()
            except:pass
            EH.Config.sys.exit(1)
            return(False)
        else:
            return(True)

# ---END OF CLASS DEF---
####################################################################

# start browser
browser = BrowserHandler().start_browser()
