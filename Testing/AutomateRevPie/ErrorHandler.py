
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
                browser.quit()
            except:pass
            sys.exit(1)
            return(False)
        else:
            return(True)
