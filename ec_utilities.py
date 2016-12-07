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

__author__ = 'fi11222'


# -------------------------------------- Logging Set-up ----------------------------------------------------------------
class EcLogger:
    cm_logger = None

    @classmethod
    def logInit(cls):
        # Creates the column headers for the CSV log file
        l_fLog = open(EcAppParam.gcm_logFile, 'w')
        l_fLog.write('LOGGER_NAME;TIME;LEVEL;MODULE;FILE;FUNCTION;LINE;MESSAGE\n')
        l_fLog.close()

        # Create the main logger
        cls.cm_logger = logging.getLogger(EcAppParam.gcm_appName)

        # One handler for the console (only up to INFO messages) and another for the CSV file (everything)
        l_handlerConsole = logging.StreamHandler()
        l_handlerFile = logging.FileHandler(EcAppParam.gcm_logFile, mode='a')

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
                    EcMailer.sendMail(
                        '{0}-{1}[{2}]/{3}'.format(
                            p_record.levelname,
                            p_record.module,
                            p_record.lineno,
                            p_record.funcName),
                        l_formatted
                    )

                    l_conn = EcConnectionPool.getNewConnection()
                    l_conn.debugData = 'EcConsoleFormatter'
                    l_cursor = l_conn.cursor()
                    try:
                        l_cursor.execute("""
                            insert into TB_MSG(
                                ST_NAME,
                                ST_LEVEL,
                                ST_MODULE,
                                ST_FILENAME,
                                ST_FUNCTION,
                                N_LINE,
                                TX_MSG
                            )
                            values('{0}', '{1}', '{2}', '{3}', '{4}', {5}, '{6}');
                        """.format(
                            p_record.name,
                            p_record.levelname,
                            p_record.module,
                            p_record.pathname,
                            p_record.funcName,
                            p_record.lineno,
                            re.sub("'", "''", re.sub('\s+', ' ', p_record.msg))
                        ))
                        l_conn.commit()
                    except Exception as e:
                        EcMailer.sendMail('TB_MSG insert failure: {0}-{1}'.format(
                            type(e).__name__,
                            repr(e)
                        ), 'Sent from EcConsoleFormatter')
                        raise

                    l_cursor.close()
                    l_conn.close()

                return l_formatted

        # Install formatters
        l_handlerConsole.setFormatter(EcConsoleFormatter('ECL:%(levelname)s:%(name)s:%(message)s'))
        l_handlerFile.setFormatter(EcCsvFormatter('"%(name)s";"%(asctime)s";"%(levelname)s";"%(module)s";' +
                                                  '"%(filename)s";"%(funcName)s";%(lineno)d;"%(message)s"'))

        # If verbose mode on, both handlers receive messages up to INFO
        if EcAppParam.gcm_verboseModeOn:
            cls.cm_logger.setLevel(logging.INFO)
            l_handlerConsole.setLevel(logging.INFO)
            l_handlerFile.setLevel(logging.INFO)

        # If debug mode is on, then the console stays as it is but the CSV file now receives everything
        if EcAppParam.gcm_debugModeOn:
            cls.cm_logger.setLevel(logging.DEBUG)
            l_handlerFile.setLevel(logging.DEBUG)

        # Install the handlers
        cls.cm_logger.addHandler(l_handlerConsole)
        cls.cm_logger.addHandler(l_handlerFile)

        # Start-up Messages
        cls.cm_logger.info('-->> Start logging')
        cls.cm_logger.debug('-->> Start logging')


g_loggerUtilities = logging.getLogger(EcAppParam.gcm_appName + '.util')
if EcAppParam.gcm_verboseModeOn:
    g_loggerUtilities.setLevel(logging.INFO)
if EcAppParam.gcm_debugModeOn:
    g_loggerUtilities.setLevel(logging.DEBUG)

# sends an e-mail through smtp
# For Amazon SES howto, see:
# http://blog.noenieto.com/blog/html/2012/06/18/using_amazon_ses_with_your_python_applications.html
class EcMailer:
    cm_sendMailGovernor = None

    @classmethod
    def initMailer(cls):
        cls.cm_sendMailGovernor = dict()

    @classmethod
    def sendMail(cls, p_subject, p_message):
        # message context with headers and body
        l_message = """From: {0}
            To: {1}
            Date: {2}
            Subject: {3}

            {4}
        """.format(
            EcAppParam.gcm_mailSender,
            ', '.join(EcAppParam.gcm_mailRecipients),
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
            l_thisSubjectHistory = cls.cm_sendMailGovernor[p_subject]
        except KeyError:
            l_thisSubjectHistory = [l_now]

        l_thisSubjectHistory.append(l_now)

        l_thisSubjectHistoryNew = list()
        l_count = 0
        for l_pastsend in l_thisSubjectHistory:
            if l_now - l_pastsend < 5*60:
                l_count += 1
                l_thisSubjectHistoryNew.append(l_pastsend)

        cls.cm_sendMailGovernor[p_subject] = l_thisSubjectHistoryNew

        # maximum : 10 with the same subject every 5 minutes
        if l_count > 10:
            # overflow stored the message in a separate file
            l_fLog = open(re.sub('\.csv', '.overflow_msg', EcAppParam.gcm_logFile), 'a')
            l_fLog.write('>>>>>>>\n' + l_message)
            l_fLog.close()
            return

        # all messages
        l_fLogName = re.sub('\.csv', '.all_msg', EcAppParam.gcm_logFile)
        l_fLog = open(l_fLogName, 'a')
        l_fLog.write('>>>>>>>\n' + l_message)
        l_fLog.close()

        l_stepPassed = 0
        try:
            # smtp client init
            if EcAppParam.gcm_amazonSmtp:
                l_smtpObj = smtplib.SMTP(
                    host=EcAppParam.gcm_smtpServer,
                    port=587,
                    timeout=10)
                l_stepPassed = 101

                l_smtpObj.starttls()
                l_stepPassed = 102

                l_smtpObj.ehlo()
                l_stepPassed = 103

                l_smtpObj.login(EcAppParam.gcm_sesUserName, EcAppParam.gcm_sesPassword)
                l_stepPassed = 104
            elif EcAppParam.gcm_gmailSmtp:
                # Gmail / TLS authentication

                # smtp client init
                l_smtpObj = smtplib.SMTP(EcAppParam.gcm_smtpServer, 587)
                l_stepPassed = 201

                # initialize TLS connection
                l_smtpObj.starttls()
                l_stepPassed = 202
                l_smtpObj.ehlo()
                l_stepPassed = 203

                # authentication
                l_smtpObj.login(EcAppParam.gcm_mailSender, EcAppParam.gcm_gmailPassword)
                l_stepPassed = 204
            else:
                l_smtpObj = smtplib.SMTP(EcAppParam.gcm_smtpServer)

            # sending message
            l_smtpObj.sendmail(EcAppParam.gcm_mailSender, EcAppParam.gcm_mailRecipients, l_message)
            l_stepPassed = 99

            # end tls session (Amazon SES or Gmail)
            if EcAppParam.gcm_amazonSmtp or EcAppParam.gcm_gmailSmtp:
                l_smtpObj.quit()
        except smtplib.SMTPException as e:
            # if failure, stores the message in a separate file
            l_fLog = open(re.sub('\.csv', '.rejected_msg', EcAppParam.gcm_logFile), 'a')
            l_fLog.write('>>>>>>>\n' + l_message)
            l_fLog.close()

            # and create a log record in another separate file (distinct from the main log file)
            l_fLog = open(re.sub('\.csv', '.smtp_error', EcAppParam.gcm_logFile), 'a')
            l_fLog.write(
                'Util;{0};CRITICAL;ec_utilities;ec_utilities.py;sendMail;113;[Step = {1}] {2}\n'.format(
                    datetime.datetime.now(tz=pytz.utc).strftime('%Y-%m-%d %H:%M.%S'),
                    l_stepPassed,
                    re.sub('\s+', ' ', + type(e).__name__ + '-' + repr(e))
                ))
            l_fLog.close()
        except Exception as e:
            l_fLog = open(l_fLogName, 'a')
            l_fLog.write('>>>>>>>\n!!!!! [Step = {0}] {1}-{2}'.format(l_stepPassed, type(e).__name__, repr(e)))
            l_fLog.close()


# ------------------------- Customized template class ------------------------------------------------------------------
def check_system_health(p_completeCheck=True):
    l_mem = psutil.virtual_memory()

    g_loggerUtilities.info('Available RAM: {0} Mb ({1} % usage)'.format(
        l_mem.available/(1024*1024), l_mem.percent))

    if l_mem.percent > 75:
        g_loggerUtilities.warning('Available RAM: {0} Mb ({1} % usage)'.format(
            l_mem.available/(1024*1024), l_mem.percent))

    if p_completeCheck:
        g_loggerUtilities.info('Complete health system check')
        l_cpu = psutil.cpu_times()
        l_swap = psutil.swap_memory()
        l_diskRoot = psutil.disk_usage('/')
        l_net = psutil.net_io_counters()
        l_processCount = len(psutil.pids())

        # log message in TB_MSG
        l_conn = EcConnectionPool.getNewConnection()
        l_conn.debugData = 'check_system_health'
        l_cursor = l_conn.cursor()
        try:
            l_cursor.execute("""
                insert into TB_MSG(
                    ST_NAME,
                    ST_LEVEL,
                    ST_MODULE,
                    ST_FILENAME,
                    ST_FUNCTION,
                    N_LINE,
                    TX_MSG
                )
                values('{0}', '{1}', '{2}', '{3}', '{4}', {5}, '{6}');
            """.format(
                'xxx',
                'XXX',
                'ec_app_core',
                './ec_app_core.py',
                'check_system_health',
                0,
                'MEM: {0}/CPU: {1}/SWAP: {2}/DISK(root): {3}/NET: {4}/PROCESSES: {5}'.format(
                    l_mem, l_cpu, l_swap, l_diskRoot, l_net, l_processCount
                )
            ))
            l_conn.commit()
        except Exception as e:
            EcMailer.sendMail('TB_EC_MSG insert failure: {0}-{1}'.format(
                type(e).__name__,
                repr(e)
            ), 'Sent from EcConsoleFormatter')
            raise

        l_cursor.close()
        l_conn.close()


# ------------------------- Customized template class ------------------------------------------------------------------
class EcTemplate(Template):
    delimiter = '§'


# ----------------- Database connection pool ---------------------------------------------------------------------------
class EcConnectionPool(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)

        self.m_connectionList = []
        self.m_getCalls = 0
        self.m_releaseCalls = 0

        if not EcAppParam.gcm_noConnectionPool:
            # lock to protect the connection pool critical sections (pick-up and release)
            self.m_connectionPoolLock = threading.Lock()
            self.m_connectionPool = []

            # fill the connection pool
            for i in range(EcAppParam.gcm_connectionPoolCount):
                l_connection = EcConnectionPool.getNewConnection()
                self.m_connectionList += [l_connection]
                self.m_connectionPool.append( l_connection )

        # starts the refresh thread
        self.refreshCounter = 0
        self.start()

    @staticmethod
    def getNewConnection():
        try:
            l_connection = EcConnector(
                user=EcAppParam.gcm_dbUser, password=EcAppParam.gcm_dbPassword,
                host=EcAppParam.gcm_dbServer,
                database=EcAppParam.gcm_dbDatabase)
        except mysql.connector.Error as l_exception:
            g_loggerUtilities.critical(
                'Cannot create connector. Exception [{0}]. Aborting.'.format(l_exception))
            raise

        l_connection.debugData = 'obtained from getNewConnection()'
        return l_connection

    def getConnection(self):
        self.m_getCalls += 1

        if EcAppParam.gcm_noConnectionPool:
            l_connection = EcConnectionPool.getNewConnection()
            self.m_connectionList += [l_connection]
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
        self.m_releaseCalls += 1

        try:
            self.m_connectionList.remove(p_connection)
        except Exception as e:
            g_loggerUtilities.info('Could not remove connection ({0}) fromm_connectionList: {1}-{2}'.format(
                p_connection.debugData,
                type(e).__name__,
                repr(e)
            ))

        if EcAppParam.gcm_noConnectionPool:
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
            #l_dummyConn = self.getConnection()
            #l_dummyConn.debugData = 'Dummy connection to test debug report'

            # sleeps for 30 seconds
            time.sleep(30)
            g_loggerUtilities.info('Refresher thread waking up ....')

            # Before anything, do a system health check (full every 5 min)
            check_system_health(self.refreshCounter%10 == 0)

            # Full open connection report every 30 s. if in debug mode
            if EcAppParam.gcm_debugModeOn:
                g_loggerUtilities.info('Full connection Report [DEBUG]')
                l_connReport = 'get/release: {0}/{1}\n'.format(self.m_getCalls, self.m_releaseCalls)
                for l_conn in self.m_connectionList:
                    l_connReport += l_conn.debugData + '\n'

                EcMailer.sendMail('Open Connections Report', l_connReport)

            # List of rotten connections every 15 minutes
            if self.refreshCounter%30 == 0:
                for l_conn in self.m_connectionList:
                    l_rottenReport = 'get/release: {0}/{1}\n'.format(self.m_getCalls, self.m_releaseCalls)
                    if l_conn.isRotten():
                        l_rottenReport += l_conn.debugData + '\n'

                    EcMailer.sendMail('Rotten Connection Report', l_rottenReport)

            self.refreshCounter += 1

            # No need to go further if no connection pool
            if EcAppParam.gcm_noConnectionPool:
                continue

            # Warning message if pool count abnormally low --> top up pool with new connections
            if len(self.m_connectionPool) < EcAppParam.gcm_connectionPoolCount/3:
                g_loggerUtilities.warning('Connections left: {0} - topping up'.format(len(self.m_connectionPool)))

                # only access to this CRITICAL SECTION one thread at a time
                # no one can get or release a connection while those in the pool are refreshed
                self.m_connectionPoolLock.acquire()

                # Add a third fill of new connections
                for i in range(EcAppParam.gcm_connectionPoolCount/3):
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
        self.m_debugData = 'Brand New'

        self.m_connectorID = EcConnector.cm_connectorCount
        EcConnector.cm_connectorCount += 1
        g_loggerUtilities.debug('Creating EcConnector #{0} ....'.format(self.m_connectorID))

        # life span = g_dbcLifeAverage +- 1/2 (in hours)
        l_lifespan = EcAppParam.gcm_dbcLifeAverage + (.5 - random.random())
        self.m_expirationDate = datetime.datetime.now(tz=pytz.utc) + datetime.timedelta(hours=l_lifespan)

        super().__init__(**kwargs)

        g_loggerUtilities.info('EcConnector #{2} created. Life span = {0:.2f} hours. Expiry: {1}'.format(
            l_lifespan, self.m_expirationDate, self.m_connectorID))

    @property
    def debugData(self):
        return '[{0}] {1}-{2}'.format(
            self.m_connectorID,
            self.m_expirationDate,
            self.m_debugData
        )
    @debugData.setter
    def debugData(self, p_debugData):
        self.m_debugData += '/' + p_debugData
        g_loggerUtilities.info('[{0}] Setting debugData: '.format(self.m_connectorID) + self.m_debugData)

    # past expiration date
    def isStale(self):
        return self.m_expirationDate < datetime.datetime.now(tz=pytz.utc)

    # 1 hour past expiration date
    def isRotten(self):
        return self.m_expirationDate < datetime.datetime.now(tz=pytz.utc) - datetime.timedelta(hours=1)

    def getID(self):
        return self.m_connectorID
