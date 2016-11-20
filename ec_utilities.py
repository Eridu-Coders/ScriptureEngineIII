# -*- coding: utf-8 -*-

import logging
import re
import mysql.connector
import time
import datetime
import pytz
import random
import threading
import smtplib
import email.utils
import psutil

from string import Template

from ec_app_params import *
from ec_local_param import *

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
                l_record = logging.LogRecord(
                    p_record.name,
                    p_record.levelno,
                    p_record.pathname,
                    p_record.lineno,
                    re.sub('"', '""', p_record.msg),
                    # message arguments are not allowed here
                    None,
                    # p_record.args,
                    p_record.exc_info,
                    p_record.funcName,
                    p_record.stack_info,
                )

                return re.sub('\s+', ' ', super().format(l_record))

        # Custom Formatter for the console --> send mail if warning or worse
        class EcConsoleFormatter(logging.Formatter):
            def format(self, p_record):
                l_formatted = super().format(p_record)

                if p_record.levelno >= logging.WARNING:
                    sendMail(
                        '{0}-{1}[{2}]/{3}'.format(
                            p_record.levelname,
                            p_record.module,
                            p_record.lineno,
                            p_record.funcName),
                        l_formatted
                    )

                return l_formatted

        # Install formatters
        l_handlerConsole.setFormatter(EcConsoleFormatter('ECL:%(levelname)s:%(name)s:%(message)s'))
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
        cls.cm_logger.info('-->> Start logging')
        cls.cm_logger.debug('-->> Start logging')


g_loggerUtilities = logging.getLogger(g_appName + '.util')
if g_verboseModeOn:
    g_loggerUtilities.setLevel(logging.INFO)
if g_debugModeOn:
    g_loggerUtilities.setLevel(logging.DEBUG)


g_sendMailGovernor = dict()


# sends an e-mail through smtp
# For Amazon SES howto, see:
# http://blog.noenieto.com/blog/html/2012/06/18/using_amazon_ses_with_your_python_applications.html
def sendMail(p_subject, p_message):
    # message context with headers and body
    l_message = """From: {0}
        To: {1}
        Date: {2}
        Subject: {3}

        {4}
    """.format(
        g_mailSender,
        ', '.join(g_mailRecipients),
        email.utils.format_datetime(datetime.datetime.now(tz=pytz.utc)),
        p_subject,
        p_message
    )

    # removes spaces at the begining of lines
    l_message = re.sub('^[ \t\r\f\v]+', '', l_message, flags=re.MULTILINE)

    # limitation of email sent
    l_now = time.time()
    try:
        # the list of all UNIX timestamps when this subject was sent in the previous 5 min at least
        l_thisSubjectHistory = g_sendMailGovernor[p_subject]
    except KeyError:
        l_thisSubjectHistory = [l_now]

    l_thisSubjectHistory.append(l_now)

    l_thisSubjectHistoryNew = list()
    l_count = 0
    for l_pastsend in l_thisSubjectHistory:
        if l_now - l_pastsend < 5*60:
            l_count += 1
            l_thisSubjectHistoryNew.append(l_pastsend)

    g_sendMailGovernor[p_subject] = l_thisSubjectHistoryNew

    # maximum : 10 with the same subject every 5 minutes
    if l_count > 10:
        # overflow stored the message in a separate file
        l_fLog = open(re.sub('\.csv', '.overflow_msg', g_logFile), 'a')
        l_fLog.write('>>>>>>>\n' + l_message)
        l_fLog.close()
        return

    # all messages
    l_fLogName = re.sub('\.csv', '.all_msg', g_logFile)
    l_fLog = open(l_fLogName, 'a')
    l_fLog.write('>>>>>>>\n' + l_message)
    l_fLog.close()

    try:
        # smtp client init
        if g_amazonSmtp:
            l_smtpObj = smtplib.SMTP(
                host=g_smtpServer,
                port=587,
                timeout=10)
            l_smtpObj.starttls()
            l_smtpObj.ehlo()
            l_smtpObj.login(g_sesUserName, g_sesPassword)
        else:
            l_smtpObj = smtplib.SMTP(g_smtpServer)

        # sending message
        l_smtpObj.sendmail(g_mailSender, g_mailRecipients, l_message)

        # end tls session (Amazon SES only)
        if g_amazonSmtp:
            l_smtpObj.quit()
    except smtplib.SMTPException as l_eception:
        # if failure, stores the message in a separate file
        l_fLog = open(re.sub('\.csv', '.rejected_msg', g_logFile), 'a')
        l_fLog.write('>>>>>>>\n' + l_message)
        l_fLog.close()

        # and create a log record in another separate file (distinct from the main log file)
        l_fLog = open(re.sub('\.csv', '.smtp_error', g_logFile), 'a')
        l_fLog.write(
            'Util;{0};CRITICAL;ec_utilities;ec_utilities.py;sendMail;113;{1}\n'.format(
                datetime.datetime.now(tz=pytz.utc).strftime('%Y-%m-%d %H:%M.%S'),
                re.sub('\s+', ' ', repr(l_eception))
            ))
        l_fLog.close()
    except Exception as e:
        l_fLog = open(l_fLogName, 'a')
        l_fLog.write('>>>>>>>\n!!!!! ' + repr(e))
        l_fLog.close()


# ------------------------- Customized template class ------------------------------------------------------------------
def check_system_health():
    l_mem = psutil.virtual_memory()

    g_loggerUtilities.info('Available RAM: {0} Mb ({1} % usage)'.format(
        l_mem.available/(1024*1024), l_mem.percent))

    if l_mem.percent > 75:
        g_loggerUtilities.warning('Available RAM: {0} Mb ({1} % usage)'.format(
            l_mem.available/(1024*1024), l_mem.percent))


# ------------------------- Customized template class ------------------------------------------------------------------
class EcTemplate(Template):
    delimiter = '§'


# ----------------- Database connection pool ---------------------------------------------------------------------------
class EcConnectionPool(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)

        if not g_noConnectionPool:
            # lock to protect the connection pool critical sections (pick-up and release)
            self.m_connectionPoolLock = threading.Lock()
            self.m_connectionPool = []

            # fill the connection pool
            for i in range(g_connectionPoolCount):
                self.m_connectionPool.append( self.getNewConnection() )

            # starts the refresh thread
            self.start()

    def getNewConnection(self):
        try:
            l_connection = EcConnector(
                user=g_dbUser, password=g_dbPassword,
                host=g_dbServer,
                database=g_dbDatabase)
        except mysql.connector.Error as l_exception:
            g_loggerUtilities.critical(
                'Cannot create connector. Exception [{0}]. Aborting.'.format(l_exception))
            raise

        return l_connection

    def getConnection(self):
        if g_noConnectionPool:
            l_connection = self.getNewConnection()
        else:
            l_connection = None

        l_tryCount = 0
        while l_connection is None:
            # only access to this CRITICAL SECTION one thread at a time
            self.m_connectionPoolLock.acquire()
            if len(self.m_connectionPool) > 0:
                l_connection = self.m_connectionPool.pop(0)

                # if the connection is past due date, create a new one
                if l_connection.isStale():
                    l_connection = self.getNewConnection()

                g_loggerUtilities.info('Connections left: {0}'.format(len(self.m_connectionPool)))
                # end of CRITICAL SECTION
                self.m_connectionPoolLock.release()
            else:
                # end of CRITICAL SECTION before rest of process
                self.m_connectionPoolLock.release()

                l_tryLimit = 5
                if l_tryCount > l_tryLimit:
                    # more than five tries --> create a new connection
                    g_loggerUtilities.warning(
                        'Failed more than {0} times to get a connection from the pool - Creating a new one'.format(
                            l_tryLimit))
                    l_connection = self.getNewConnection()
                else:
                    # otherwise wait for 1 second fo other connections to be released
                    l_tryCount += 1
                    g_loggerUtilities.info('Sleeping ...')
                    time.sleep(1)

        return l_connection

    def releaseConnection(self, p_connection):
        if g_noConnectionPool:
            p_connection.close()
        else:
            # only access this CRITICAL SECTION one thread at a time
            self.m_connectionPoolLock.acquire()
            self.m_connectionPool.append(p_connection)
            g_loggerUtilities.info('Connections left: {0}'.format(len(self.m_connectionPool)))
            # end of CRITICAL SECTION
            self.m_connectionPoolLock.release()

    # refresher thread
    def run(self):
        g_loggerUtilities.info('Connection refresh thread started ...')
        while True:
            # sleeps for 30 seconds
            time.sleep(30)
            g_loggerUtilities.info('Hello')

            # Before anything, do a system health check
            check_system_health()

            # Warning message if pool count abnormally low --> top up pool with new connections
            if len(self.m_connectionPool) < g_connectionPoolCount/3:
                g_loggerUtilities.warning('Connections left: {0} - topping up'.format(len(self.m_connectionPool)))

                # only access to this CRITICAL SECTION one thread at a time
                # no one can get or release a connection while those in the pool are refreshed
                self.m_connectionPoolLock.acquire()

                # Add a third fill of new connections
                for i in range(g_connectionPoolCount/3):
                    g_loggerUtilities.info('topping up: {0}'.format(i))
                    self.m_connectionPool.append( self.getNewConnection() )

                # end of CRITICAL section
                self.m_connectionPoolLock.release()

            g_loggerUtilities.info('Starting refresh cycle')

            # refresh one randomly chosen connection if stale

            # only access to this CRITICAL SECTION one thread at a time
            # no one can get or release a connection while those in the pool are refreshed
            self.m_connectionPoolLock.acquire()

            # CRITICAL SECTION
            l_testIndex = random.randint(0, len(self.m_connectionPool)-1)

            # CRITICAL SECTION
            if self.m_connectionPool[l_testIndex].isStale():
                g_loggerUtilities.debug('Stale connection found')
                self.m_connectionPool[l_testIndex] = self.getNewConnection()
            else:
                g_loggerUtilities.debug('No stale connection found')

            # end of CRITICAL section
            self.m_connectionPoolLock.release()

            g_loggerUtilities.info('End of refresh cycle')


# custom DB connector class incorporating expiration date
class EcConnector(mysql.connector.MySQLConnection):
    cm_connectorCount = 0

    @classmethod
    def classInit(cls):
        cls.cm_connectorCount = 0
        g_loggerUtilities.info('EcConnector initialized. cm_connectorCount = {0}'.format(cls.cm_connectorCount))

    def __init__(self, **kwargs):
        self.m_connectorID = EcConnector.cm_connectorCount
        g_loggerUtilities.debug('Creating EcConnector #{0} ....'.format(self.m_connectorID))
        EcConnector.cm_connectorCount += 1

        # life span = g_dbcLifeAverage +- 1/2 (in hours)
        l_lifespan = g_dbcLifeAverage + (.5 - random.random())
        self.m_expirationDate = datetime.datetime.now(tz=pytz.utc) + datetime.timedelta(hours=l_lifespan)

        super().__init__(**kwargs)

        g_loggerUtilities.info('EcConnector #{2} created. Life span = {0:.2f} hours. Expiry: {1}'.format(
            l_lifespan, self.m_expirationDate, self.m_connectorID))

    def isStale(self):
        return self.m_expirationDate < datetime.datetime.now(tz=pytz.utc)

    def getID(self):
        return self.m_connectorID
