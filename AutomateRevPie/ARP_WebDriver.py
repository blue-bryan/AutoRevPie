#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-Created on Thu Jun  6 21:22:43 2019
-@author: bryan
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions

import getpass
import traceback

import lxml.html
import bs4

import AutomateRevPie.config as Config

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
        with open(_fpath, 'a') as _f:
            print(Config.datetime.datetime.now(), '\n' + ('-' * 20), message, file=_f)
            print(str(err), file=_f)
            print(traceback.format_exc(), file=_f)

    def getLogFile(self):
        try:
            with open ((Config.config_path+"/config.ini"), 'r') as _f:
                    _logsPath = Config.os.path.realpath(
                                Config.os.path.join(_f.readline(), "logs.txt"))
        except:
            _logsPath=Config.config_path+"/error_logs.txt"
        return(_logsPath)

    def waiting(self, duration):
        ''' Will call time.sleep(duration) and handle KeyboardInterrupt exceptions.
        '''
        try:
            Config.time.sleep(duration)
        except KeyboardInterrupt as err:
            self.printToLog("\n"
                        , err, self.getLogFile())
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
                        , err, self.getLogFile())
        except KeyboardInterrupt as err:
            self.printToLog("\n"
                        , err, self.getLogFile())
            Config.sys.exit(1)

    def checkBrowser(self):
        ''' Will call webdriver.title to check if browser is currently open and responding.
            If not, handles exceptions and exits program.
        '''
        try:
            browser.title
        except Exception as err:
            self.printToLog("\n\ncheckBrowser: Error, closing...\n"
                    , err, self.getLogFile())
            try:
                browser.quit()
            except:pass
            Config.sys.exit(1)
            return(False)
        else:
            return(True)

# ---END OF CLASS DEF---
####################################################################

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
                    , err, ErrorHandler().getLogFile())
        Config.sys.exit(1)

def getLoginInfo(_option):
    ''' - accepted values for _option: '-u' || '-p'
    '''
    if _option == '-u':
        try:
            u = input("\n Input Admin Username: ")
            return(u)
        except KeyboardInterrupt:
            print("\n")
            Config.sys.exit(1)
        except Exception as err:
            ErrorHandler().printToLog("\n\nError during user input, closing...\n"
                        , err, ErrorHandler().getLogFile())
            Config.sys.exit(1)
    elif _option == '-p':
        try:
            p = getpass.getpass(prompt="  password: ")
            # admin_pass = input("  password: ")
            print("\n . . . \n")
            return(p)
        except KeyboardInterrupt:
            print("\n")
            Config.sys.exit(1)
        except Exception as err:
            ErrorHandler().printToLog("\n\nError during user input, closing...\n"
                        , err, ErrorHandler().getLogFile())
            Config.sys.exit(1)

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
                , err, ErrorHandler().getLogFile())
        ErrorHandler().checkBrowser()
        Config.sys.exit(1)
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
                , err, ErrorHandler().getLogFile())
        ErrorHandler().checkBrowser()
        Config.sys.exit(1)
    else:
        text_area = browser.find_element_by_xpath("//input[@name='userName']")
        text_area.send_keys(username)
        text_area = browser.find_element_by_xpath("//input[@name='passWord']")
        text_area.send_keys(password)

        browser.find_element_by_xpath("//button[@value='Submit']").click()
        ErrorHandler().waiting(1)

# ******************************************************************

browser = start_browser()


