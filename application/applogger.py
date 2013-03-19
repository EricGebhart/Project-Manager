
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
   This is a class to manage logging
"""

__author__ = 'Eric Gebhart <e.a.gebhart@gmail.com>'
__support__ = 'Eric Gebhart <e.a.gebhart@gmail.com>'
__version__ = '$Revision: 1 $'[11:-2]
__application__ = 'applicationlogger'    # we don't have a name yet...

import logging


class applicationlogger():
    def __init__(self):
        self.logger = logging.getLogger(__application__)

        self.logger.setLevel(logging.WARNING)
        self.logger_levels = {'warning':    logging.WARNING,
                              'info':       logging.INFO,
                              'error':      logging.ERROR,
                              'critical':   logging.CRITICAL,
                              'debug':      logging.DEBUG,
                              }

        #Set up human interface options for argparse.
        self.logger_choices = []

        for key in self.logger_levels:
            self.logger_choices.append(key)

    def debug(self, message):
        self.logger.debug(message)

    def critical(self, message):
        self.logger.critical(message)

    def error(self, message):
        self.logger.error(message)

    def info(self, message):
        self.logger.info(message)

    def warning(self, message):
        self.logger.warning(message)

    def get_logger(self):
        return(self.logger)

    def get_choices(self):
        return(self.logger_choices)

    def setLevel(self, level):
        self.logger.setLevel(self.logger_levels[level])

    def setup(self, formatter):
        #hdlr = logging.FileHandler('/var/tmp/%s.log' % __application__)
        self.stdio_hdlr = logging.StreamHandler()

        self.stdio_hdlr.setFormatter(formatter)
        self.logger.addHandler(self.stdio_hdlr)

    def quiet(self):
        logger.removeHandler(self.stdio_hdlr)

    def logfile(self, logfile, formatter):
        # hdlr = logging.FileHandler('/var/tmp/%s.log' % __application__)
        hdlr = logging.FileHandler(logfile, encoding='utf-8')
        hdlr.setFormatter(formatter)
        logger.addHandler(hdlr)

    def formatter(self, format):
        return logging.Formatter(format)

applogger = applicationlogger()
logger = applogger.get_logger()
