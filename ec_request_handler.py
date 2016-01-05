# -*- coding: utf-8 -*-

import http.server
import datetime
import pytz
import sys
import json
import random
import urllib.parse
import hashlib

from ec_utilities import *

__author__ = 'fi11222'


# ----------------------------------------- New Request Handler --------------------------------------------------------
class EcRequestHandler(http.server.SimpleHTTPRequestHandler):
    # lock to protect the critical section where new Terminal UIDs are created
    cm_termIDCreationLock = None

    # browscap data structure
    cm_browscap = None

    # app-specific object
    cm_appCore = None

    # database connection pool
    cm_connectionPool = None

    @classmethod
    def initClass(cls, p_browscap, p_appCore):
        cls.cm_termIDCreationLock = threading.Lock()
        cls.cm_browscap = p_browscap
        cls.cm_appCore = p_appCore

        cls.cm_connectionPool = EcConnectionPool()

    def __init__(self, p_request, p_client_address, p_server):
        # each instance has its own logger with a name that includes the thread it is riding on
        self.m_logger = logging.getLogger(g_appName + '.HR-' + threading.current_thread().name)
        if g_verboseModeOn:
            self.m_logger.setLevel(logging.INFO)
        if g_debugModeOn:
            self.m_logger.setLevel(logging.DEBUG)

        # the unique identifier of the browser (called here a "terminal")
        self.m_terminalID = None

        # flag indicating that the cookie is to be destroyed when the headers are generated
        self.m_delCookie = None

        # terminal (browser) characteristics
        self.m_browser = ''
        self.m_platform = ''
        self.m_renderingEngine = ''
        self.m_browserVersion = ''
        self.m_platformDesc = ''
        self.m_devMaker = ''
        self.m_devName = ''

        # the request headers
        self.m_headersDict = {}

        # the current context
        self.m_contextDict = {}
        # the previous context, as retrieved from the TB_TERMINAL table
        self.m_previousContext = {}

        super().__init__(p_request, p_client_address, p_server)
        self.m_logger.info('------------ request handler created ------------------------------------')

    def do_GET(self):
        # pick a DB connection from the pool
        l_dbConnection = EcRequestHandler.cm_connectionPool.getConnection()

        l_clientIpPort = self.client_address[0] + ':' + str(self.client_address[1])
        self.m_logger.info('------------ do_Get() ------------------------------------')
        self.m_logger.info('Thread name      : {0}'.format(threading.currentThread().getName()))
        self.m_logger.info('Client Address   : {0}'.format(l_clientIpPort))
        self.m_logger.info('Request Path     : {0}'.format(self.path))
        self.m_logger.info('Request Line     : {0}'.format(self.requestline))

        # -------------------------- User Agent / Browscap analysis ----------------------------------------------------
        l_headers = str(self.headers).strip()
        self.m_logger.debug('Headers          : {0}'.format(l_headers))

        l_queryString = ''
        try:
            l_queryString = re.findall('\?([^ ]+)', self.requestline)[0]
        except LookupError:
            pass
        self.m_logger.info('Query String     : {0}'.format(l_queryString))

        # parse_qs returns values which are lists
        l_parseDict = urllib.parse.parse_qs(l_queryString)
        # since there is ever only one value per argument, take first value of each list
        self.m_contextDict = dict((k, v[0]) for k, v in l_parseDict.items())

        self.m_logger.info('Context Dict.    : {0}'.format(self.m_contextDict))

        # pyCharm complains but this is perfectly ok
        self.m_logger.debug('Raw headers      : {0}'.format(l_headers))
        self.m_headersDict = dict(re.findall(r"(?P<key>.*?): (?P<value>.*?)\n", l_headers + '\n'))
        self.m_logger.info('Headers dict.    : {0}'.format(self.m_headersDict))

        l_userAgent = ''

        # browser (terminal) attributes based on user-agent through browscap
        if 'User-Agent' in self.m_headersDict.keys():
            self.m_logger.info('User-Agent       : {0}'.format(self.m_headersDict['User-Agent']))
            l_userAgent = self.m_headersDict['User-Agent']

            # browscap can be None during debug (parameter p_skip=True in initBrowscap)
            if EcRequestHandler.cm_browscap is not None:
                l_browscap = EcRequestHandler.cm_browscap.search(self.m_headersDict['User-Agent'])

                if l_browscap is None:
                    self.m_logger.warning('No Browscap info found!')
                else:
                    self.m_browser = l_browscap.name()
                    self.m_platform = l_browscap.platform()
                    self.m_renderingEngine = l_browscap.rendering_engine_name()
                    self.m_browserVersion = str(l_browscap.version())
                    self.m_platformDesc = l_browscap.platform_description()
                    self.m_devMaker = l_browscap.device_maker()
                    self.m_devName = l_browscap.device_name()

                    self.m_logger.info('Browser Name     : {0}'.format(self.m_browser))
                    self.m_logger.info('Version          : {0}'.format(self.m_browserVersion))
                    self.m_logger.info('Browser Category : {0}'.format(l_browscap.category()))
                    self.m_logger.info('Rendering Engine : {0}'.format(self.m_renderingEngine))
                    self.m_logger.info('OS Platform      : {0}'.format(self.m_platform))

                    self.m_logger.info('Device Maker     : {0}'.format(self.m_devMaker))
                    self.m_logger.info('Device Name      : {0}'.format(self.m_devName))
                    self.m_logger.info('Platform Desc.   : {0}'.format(self.m_platformDesc))
                    self.m_logger.info('Platform Version : {0}'.format(l_browscap.platform_version()))

        else:
            self.m_logger.warning('No User-Agent in : {0}'.format(repr(l_headers)))

        # ------------------------------------- Language ---------------------------------------------------------------
        if 'Accept-Language' in self.m_headersDict.keys():
            l_acceptLanguage = self.m_headersDict['Accept-Language']
            self.m_logger.info('Accept Language  : {0}'.format(l_acceptLanguage))

            # only recognizes French. Otherwise, English
            if re.search('fr', l_acceptLanguage) is not None:
                self.m_contextDict['z'] = 'fr'
            else:
                self.m_contextDict['z'] = 'en'
        elif 'Accept Language' in self.m_headersDict.keys():
            l_acceptLanguage = self.m_headersDict['Accept Language']
            self.m_logger.info('Accept Language  : {0}'.format(l_acceptLanguage))

            # only recognizes French. Otherwise, English
            if re.search('fr', l_acceptLanguage) is not None:
                self.m_contextDict['z'] = 'fr'
            else:
                self.m_contextDict['z'] = 'en'
        else:
            self.m_contextDict['z'] = 'en'

        # ------------------------------------- Cookies ----------------------------------------------------------------
        if 'Cookie' in self.m_headersDict.keys():
            # only one cookie used, to store existing Terminal ID (if any)
            l_cookieString = str(self.m_headersDict['Cookie'])
            self.m_logger.info('Raw Cookie string: {0}'.format(l_cookieString))

            l_cookieKey = (l_cookieString.split('=')[0]).strip()
            l_cookieValue = (l_cookieString.split('=')[1]).strip()

            if l_cookieKey != g_sessionName:
                # this can happen if there is a version change and old cookies remain at large
                self.m_logger.warning('Cookie found but wrong name: "{0}" Should be "{1}"'.format(
                    l_cookieKey, g_sessionName))
                # in this case, the cookie is to be destroyed, before a new one is created
                self.m_delCookie = l_cookieKey
            else:
                # the proper cookie has been found
                self.m_logger.info('Terminal ID (old): {0}'.format(l_cookieValue))
                self.m_terminalID = l_cookieValue

        # Retrieves previous context if any and cancels Terminal ID if none found
        if self.m_terminalID is not None:
            self.m_logger.debug('Attempting to recover previous context')
            l_query = """
                select TX_CONTEXT
                from TB_TERMINAL
                where TERMINAL_ID = '{0}'
                ;""".format(self.m_terminalID)

            try:
                l_cursor = l_dbConnection.cursor(buffered=True)
                l_cursor.execute(l_query)
                self.m_logger.debug('Rowcount         : {0}'.format(l_cursor.rowcount))

                # if no rows were found, it means that the terminal ID is absent from the table --> create a new one
                if l_cursor.rowcount == 0:
                    self.m_terminalID = None
                else:
                    # retrieve former context
                    for l_context, in l_cursor:
                        self.m_logger.info('Previous context : {0}'.format(l_context))
                        self.m_previousContext = json.loads(l_context)

                l_cursor.close()
            except Exception as l_exception:
                self.m_logger.warning('Something went wrong {0}'.format(l_exception.args))
                self.m_terminalID = None

        # create new terminal ID if required
        if self.m_terminalID is None or self.m_terminalID == '':
            self.m_logger.debug('Thread [{0}] before lock'.format(threading.currentThread().getName()))

            # make sure that only one thread at a time has access to this CRITICAL section
            EcRequestHandler.cm_termIDCreationLock.acquire()
            self.m_logger.debug('Thread [{0}] after lock'.format(threading.currentThread().getName()))

            l_created = False
            l_attemptCount = 0
            # will make 100 attempts max to create a new unique terminal ID
            while not l_created and l_attemptCount < 100:
                l_attemptCount += 1

                # the Id string is a hash of the user-agent, the ip and a random number
                l_hash = hashlib.new('MD5')
                l_hash.update(bytes(l_userAgent + l_clientIpPort + str(random.random()), 'utf-8'))

                self.m_terminalID = l_hash.hexdigest()
                self.m_logger.info('Terminal ID (new): {0}'.format(self.m_terminalID))

                l_query = """
                    insert into TB_TERMINAL(TERMINAL_ID, DT_CREATION, DT_LAST_UPDATE, TX_CONTEXT)
                    values('{0}', NOW(), NOW(), '{1}')
                    ;""".format(self.m_terminalID,
                                json.dumps(self.m_contextDict,
                                           ensure_ascii=False).replace("'", "''").replace("\\", "\\\\"))

                self.m_logger.debug('l_query: {0}'.format(l_query))
                # assume it will work but can revert to False if failure
                l_created = True
                try:
                    l_cursor = l_dbConnection.cursor()
                    l_cursor.execute(l_query)
                    # the cursor is executed and THEN, the connection is committed
                    l_dbConnection.commit()
                    l_cursor.close()
                except Exception as l_exception:
                    # will go here if the row could not be inserted because the ID already existed
                    self.m_logger.warning('Something went wrong {0}'.format(l_exception.args))
                    l_created = False

            self.m_logger.debug('Thread [{0}] waiting'.format(threading.currentThread().getName()))

            # END OF CRITICAL SECTION
            EcRequestHandler.cm_termIDCreationLock.release()
            self.m_logger.debug('Thread [{0}] released lock'.format(threading.currentThread().getName()))

        if self.m_terminalID is None or self.m_terminalID == '':
            # abort application if no Id could be created despite all that
            self.m_logger.critical('Could not retrieve or create Terminal ID. Recovery impossible.')
            sys.exit()

        self.m_logger.info('Terminal ID      : {0}'.format(self.m_terminalID))

        # -------------------------------- Log -------------------------------------------------------------------------

        l_query = """
            insert into TB_LOG(
                `TERMINAL_ID`
                , `ST_IP`
                , `N_PORT`
                , `ST_BROWSER`
                , `ST_BRW_VERSION`
                , `ST_RENDERING_ENGINE`
                , `ST_PLATFORM`
                , `ST_PLTF_DESC`
                , `ST_DEV_NAME`
                , `ST_DEV_MAKER`
                , `TX_PATH`
                , `TX_CONTEXT`
            )
            values('{0}', '{1}', {2}, '{3}', '{4}', '{5}', '{6}', '{7}', '{8}', '{9}', '{10}', '{11}')
            ;""".format(
                self.m_terminalID,
                self.client_address[0],
                self.client_address[1],
                self.m_browser.replace("'", "''"),
                self.m_browserVersion.replace("'", "''"),
                self.m_renderingEngine.replace("'", "''"),
                self.m_platform.replace("'", "''"),
                self.m_platformDesc.replace("'", "''"),
                self.m_devName.replace("'", "''"),
                self.m_devMaker.replace("'", "''"),
                self.path,
                json.dumps(self.m_contextDict).replace("'", "''"))
        try:
            l_cursor = l_dbConnection.cursor()
            l_cursor.execute(l_query)
            # the cursor is executed and THEN, the connection is committed
            l_dbConnection.commit()
            l_cursor.close()
        except Exception as l_exception:
            self.m_logger.warning('Something went wrong {0}'.format(l_exception.args))

        # ---------------------------------- Response ------------------------------------------------------------------
        if re.match('/static/', self.path):
            # fetching a static document --> rely on the base class functionality
            super().do_GET()
        elif re.match('/favicon.ico', self.path):
            # redirect favicon fetch to the appropriate location
            self.path = 'static/images/favicon.ico'
            super().do_GET()
        elif self.path == '/' or re.match('/\?', self.path):
            # this is the application call
            self.buildResponse(l_dbConnection)
        else:
            # anything else is an error
            super().send_error(404, 'Only valid path starts with /static/')

        # ---------------------------------- Release DB connection -----------------------------------------------------
        EcRequestHandler.cm_connectionPool.releaseConnection(l_dbConnection)

    def end_headers(self):
        # cookie destruction if necessary
        if self.m_delCookie is not None:
            l_cookieString = '{0}=deleted; Domain={1}; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT'.format(
                self.m_delCookie, g_appDomain)
            self.send_header('Set-Cookie', l_cookieString)

        # send the cookie containing the terminal ID in the headers
        if self.m_terminalID is None:
            self.m_logger.warning('Terminal ID undefined')
        else:
            # hundred year cookie (duration in g_cookiePersistence)
            l_expire = (datetime.datetime.now(tz=pytz.utc) +
                        datetime.timedelta(g_cookiePersistence)).strftime('%a, %d %b %Y %H:%M:%S %Z')

            l_cookieString = '{0}={1}; Domain={2}; Path=/; Expires={3}; HttpOnly'\
                .format(g_sessionName, self.m_terminalID, g_appDomain, l_expire)

            self.send_header('Set-Cookie', l_cookieString)

        super().end_headers()

    def buildResponse(self, p_dbConnection):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

        # call the rest of the app to get the appropriate response
        l_response, l_newDict = \
            EcRequestHandler.cm_appCore.getResponse(
                self.m_previousContext, self.m_contextDict, EcRequestHandler.cm_connectionPool)
        self.wfile.write(bytes(l_response, 'utf-8'))

        # store the final context (possibly modified by the app)
        l_query = """
            update TB_TERMINAL
            set
                DT_LAST_UPDATE = NOW(),
                TX_CONTEXT = '{0}'
            where TERMINAL_ID = '{1}'
            ;""".format(json.dumps(self.m_contextDict,
                                   ensure_ascii=False).replace("'", "''").replace("\\", "\\\\"),
                        self.m_terminalID)

        try:
            l_cursor = p_dbConnection.cursor()
            l_cursor.execute(l_query)
            # the cursor is executed and THEN, the connection is committed
            p_dbConnection.commit()
            l_cursor.close()
        except Exception as l_exception:
            self.m_logger.warning('Something went wrong {0}'.format(l_exception.args))
