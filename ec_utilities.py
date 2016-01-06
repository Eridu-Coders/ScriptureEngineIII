# -*- coding: utf-8 -*-

import logging
import re
import mysql.connector
import time
import datetime
import pytz
import random
import threading

from ec_app_params import *

__author__ = 'fi11222'


# -------------------------------------- Logging Set-up ----------------------------------------------------------------
class EcLogger:
    cm_logger = None

    @classmethod
    def logInit(cls):
        # Creates the column headers for the CSV log file
        l_fLog = open(g_logFile, 'w')
        l_fLog.write('LOGGER_NAME;TIME;LEVEL;MODULE;FILE;FUNCTION;LINE;MESSAGE\n')
        l_fLog.close()

        # Create the main logger
        cls.cm_logger = logging.getLogger(g_appName)

        # One handler for the console (only up to INFO messages) and another for the CSV file (everything)
        l_handlerConsole = logging.StreamHandler()
        l_handlerFile = logging.FileHandler(g_logFile, mode='a')

        # Custom Formatter for the CSV file --> eliminates multiple spaces (and \r\n)
        class EcCsvFormatter(logging.Formatter):
            def format(self, p_record):
                return re.sub('\s+', ' ', super().format(p_record))

        # Install formatters
        l_handlerConsole.setFormatter(logging.Formatter('ECL:%(levelname)s:%(name)s:%(message)s'))
        l_handlerFile.setFormatter(EcCsvFormatter('"%(name)s";"%(asctime)s";"%(levelname)s";"%(module)s";' +
                                                  '"%(filename)s";"%(funcName)s";%(lineno)d;"%(message)s"'))

        # If verbose mode on, both handlers receive messages up to INFO
        if g_verboseModeOn:
            cls.cm_logger.setLevel(logging.INFO)
            l_handlerConsole.setLevel(logging.INFO)
            l_handlerFile.setLevel(logging.INFO)

        # If debug mode is on, then the console stays as it is but the CSV file now receives everything
        if g_debugModeOn:
            cls.cm_logger.setLevel(logging.DEBUG)
            l_handlerFile.setLevel(logging.DEBUG)

        # Install the handlers
        cls.cm_logger.addHandler(l_handlerConsole)
        cls.cm_logger.addHandler(l_handlerFile)

        # Start-up Messages
        cls.cm_logger.info('Start logging')
        cls.cm_logger.debug('Start logging')


g_loggerUtilities = logging.getLogger(g_appName + '.util')
if g_verboseModeOn:
    g_loggerUtilities.setLevel(logging.INFO)
if g_debugModeOn:
    g_loggerUtilities.setLevel(logging.DEBUG)


# ----------------- Database connection pool ------------------------------------------------------
class EcConnectionPool(threading.Thread):
    def __init__(self):
        super().__init__()

        # lock to protect the connection pool critical sections (pick-up and release)
        self.m_connectionPoolLock = threading.Lock()
        self.m_connectionPool = set()

        # fill the connection pool
        for i in range(g_connectionPoolCount):
            self.m_connectionPool.add(
                # mysql.connector.connect(
                EcConnector(
                    user=g_dbUser, password=g_dbPassword,
                    host=g_dbServer,
                    database=g_dbDatabase)
            )

        self.start()

    def getConnection(self):
        l_connection = None
        while l_connection is None:
            # only access to this CRITICAL section one thread at a time
            self.m_connectionPoolLock.acquire()
            if len(self.m_connectionPool) > 0:
                l_connection = self.m_connectionPool.pop()

                g_loggerUtilities.info('Connections left: {0}'.format(len(self.m_connectionPool)))
                # end of CRITICAL section
                self.m_connectionPoolLock.release()
            else:
                # end of CRITICAL section before sleep
                self.m_connectionPoolLock.release()

                g_loggerUtilities.info('Sleeping ...')
                # otherwise wait for 1 second fo other connections to be released
                time.sleep(1)

        return l_connection

    def releaseConnection(self, p_connection):
        # only access this CRITICAL section one thread at a time
        self.m_connectionPoolLock.acquire()
        self.m_connectionPool.add(p_connection)
        g_loggerUtilities.info('Connections left: {0}'.format(len(self.m_connectionPool)))
        # end of CRITICAL section
        self.m_connectionPoolLock.release()

    def run(self):
        g_loggerUtilities.info('Connection refresh thread started ...')
        while True:
            # sleeps for 15 minutes
            time.sleep(15*60)
            g_loggerUtilities.info('Starting refresh cycle')

            l_tmpSet = set()
            while True:
                # only access to this CRITICAL section one thread at a time
                # no one can get or release a connection while those in the pool are refreshed
                self.m_connectionPoolLock.acquire()
                if len(self.m_connectionPool) == 0:
                    break

                l_connection = self.m_connectionPool.pop()
                # end of CRITICAL section before rest of loop
                self.m_connectionPoolLock.release()

                if l_connection.isStale():
                    g_loggerUtilities.info('Stale connection found')
                    l_connection = EcConnector(
                        user=g_dbUser, password=g_dbPassword,
                        host=g_dbServer,
                        database=g_dbDatabase)

                l_tmpSet.add(l_connection)

            # when this point is reach the critical section is still in effect
            self.m_connectionPool = l_tmpSet

            # end of CRITICAL section before sleep
            self.m_connectionPoolLock.release()
            g_loggerUtilities.info('End of refresh cycle')


class EcConnector(mysql.connector.MySQLConnection):
    def __init__(self, **kwargs):
        # life span = g_dbcLifeAverage +- 1/2 (in hours)
        l_lifespan = g_dbcLifeAverage + (.5 - random.random())
        self.m_expirationDate = datetime.datetime.now(tz=pytz.utc) + datetime.timedelta(hours=l_lifespan)

        g_loggerUtilities.info('EcConnector created. Life span = {0:.2f} hours. Expiry: {1}'.format(
            l_lifespan, self.m_expirationDate))

        super().__init__(**kwargs)

    def isStale(self):
        return self.m_expirationDate > datetime.datetime.now(tz=pytz.utc)
