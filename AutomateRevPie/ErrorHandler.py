#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-Created on Thu Jun  6 21:22:43 2019
-@author: bryan
"""

import traceback

import AutomateRevPie.config as Config

class Handler:
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
            Config.sys.exit(1)

# ---END OF CLASS DEF---
####################################################################
