# -*- coding: utf-8 -*-

import http.server
import sys
import json
import urllib.parse
import hashlib

from ec_app_core import *

#import se3_utilities

__author__ = 'fi11222'


g_loggerHandler = logging.getLogger(EcAppParam.gcm_appName + '.rq_handler')
if EcAppParam.gcm_verboseModeOn:
    g_loggerHandler.setLevel(logging.INFO)
if EcAppParam.gcm_debugModeOn:
    g_loggerHandler.setLevel(logging.DEBUG)


# ----------------------------------------- New Request Handler --------------------------------------------------------
class EcRequestHandler(http.server.SimpleHTTPRequestHandler):
    cm_handlerCount = 0

    # lock to protect the critical section where new Terminal UIDs are created
    cm_termIDCreationLock = None

    # browscap data structure
    cm_browscap = None

    # app-specific object
    cm_appCore = None

    # database connection pool
    cm_connectionPool = None

    # Template string for the browser test page
    cm_browserTestPage = ''

    # Template string for the bad browser message page
    cm_badBrowserPage = ''

    @classmethod
    def initClass(cls, p_browscap, p_appCore, p_browserTestPath, p_badBrowserPath):
        cls.cm_termIDCreationLock = threading.Lock()
        cls.cm_browscap = p_browscap
        cls.cm_appCore = p_appCore

        cls.cm_connectionPool = p_appCore.getConnectionPool()

        # load browser test templates string
        try:
            with open(p_browserTestPath, 'r') as l_fTemplate:
                cls.cm_browserTestPage = l_fTemplate.read()
        except OSError as e:
            g_loggerHandler.critical(
                'Could not open template file [{0}]. Exception: [{1}]. Aborting.'.format(
                    p_browserTestPath, repr(e)))
            raise

        g_loggerHandler.info('Loaded template file [{0}]. Len = {1}'.format(
            p_browserTestPath, len(cls.cm_browserTestPage)))

        # load bad browser message templates string
        try:
            with open(p_badBrowserPath, 'r') as l_fTemplate:
                cls.cm_badBrowserPage = l_fTemplate.read()
        except OSError as e:
            g_loggerHandler.critical(
                'Could not open bad browser file [{0}]. Exception: [{1}]. Aborting.'.format(
                    p_badBrowserPath, repr(e)))
            raise

        g_loggerHandler.info('Loaded bad browser file [{0}]. Len = {1}'.format(
            p_badBrowserPath, len(cls.cm_badBrowserPage)))

    def __init__(self, p_request, p_client_address, p_server):
        self.m_handlerID = EcRequestHandler.cm_handlerCount
        EcRequestHandler.cm_handlerCount += 1

        # each instance has its own logger with a name that includes the thread it is riding on
        self.m_logger = logging.getLogger(EcAppParam.gcm_appName + '.HR-' + threading.current_thread().name)
        if EcAppParam.gcm_verboseModeOn:
            self.m_logger.setLevel(logging.INFO)
        if EcAppParam.gcm_debugModeOn:
            self.m_logger.setLevel(logging.DEBUG)

        # the unique identifier of the browser (called here a "terminal")
        self.m_terminalID = None

        # flag indicating that the terminal has the required cookies & JavaScript capabilities
        self.m_validatedTerminal = False

        # flag indicating that the terminal does not have the required capabilities (cookies, JS)
        self.m_badTerminal = False

        # reason for bad browser determination, if any
        self.m_reason = ''

        # flag indicating that the cookie is to be destroyed when the headers are generated
        self.m_delCookie = None

        # flag indicating that do_Get has been called (in case m_terminalID is found missing when needed)
        self.m_doGetCalled = False

        self.m_userAgent = ''

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

        self.m_logger.info('------------ request handler #{0} created -----------------------------'.format(
            self.m_handlerID))

        super().__init__(p_request, p_client_address, p_server)

    # disable logging to std output
    def log_message(self, *args):
        pass

    def pack_massage(self, p_message):
        l_message = p_message

        l_message += '\n--------- Context ------------\n'
        l_message += '- IP ---> [{0}]\n'.format(self.client_address[0])
        l_message += '- Port ---> [{0}]\n'.format(self.client_address[1])

        if EcRequestHandler.cm_browscap is not None:
            l_message += '= Browser ---> [{0}]\n'.format(self.m_browser)
            l_message += '= Platform ---> [{0}]\n'.format(self.m_platform)
            l_message += '= Rendering Eng ---> [{0}]\n'.format(self.m_renderingEngine)
            l_message += '= Version ---> [{0}]\n'.format(self.m_browserVersion)
            l_message += '= Platform Desc ---> [{0}]\n'.format(self.m_platformDesc)
            l_message += '= Dev Maker ---> [{0}]\n'.format(self.m_devMaker)
            l_message += '= Dev Name ---> [{0}]\n'.format(self.m_devName)

        l_message += '+ request line ---> [{0}]\n'.format(self.requestline)
        l_message += '+ raw context ---> [{0}]\n'.format(self.m_contextDict)
        l_message += '+ headers ---> [{0}]\n'.format(str(self.headers).strip())
        l_message += '+ headers dict ---> [{0}]\n'.format(self.m_headersDict)

        return l_message

    def do_HEAD(self):
        super().do_HEAD()

    def do_GET(self):
        self.m_doGetCalled = True

        # pick a DB connection from the pool
        l_dbConnection = EcRequestHandler.cm_connectionPool.getConnection()
        l_dbConnection.debugData = 'EcRequestHandler.do_GET main working connection'

        l_clientIpPort = self.client_address[0] + ':' + str(self.client_address[1])
        self.m_logger.info('------------ do_Get() START ------------------------------------')
        self.m_logger.info('Handler ID       : {0}'.format(self.m_handlerID))
        self.m_logger.info('Connection ID    : {0}'.format(l_dbConnection.getID()))
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

        # Extraction of k/v pairs from headers
        self.m_logger.debug('Raw headers      : {0}'.format(l_headers))
        # key is converted to lower case to handle the "user-agent" vs. "User-Agent" case
        self.m_headersDict = dict(
            (k.lower(), v) for k, v in
            re.findall(r"(?P<key>.*?): (?P<value>.*?)\n", l_headers + '\n'))
        self.m_logger.info('Headers dict.    : {0}'.format(self.m_headersDict))

        # browser (terminal) attributes based on user-agent through browscap
        if 'user-agent' in self.m_headersDict.keys():
            self.m_logger.info('User-Agent       : {0}'.format(self.m_headersDict['user-agent']))
            self.m_userAgent = self.m_headersDict['user-agent']

            # browscap can be None during debug (parameter p_skip=True in initBrowscap)
            if EcRequestHandler.cm_browscap is not None:
                l_browscap = EcRequestHandler.cm_browscap.search(self.m_headersDict['user-agent'])

                if l_browscap is None:
                    self.m_browser = '<Browscap info nor found>'
                    self.m_platform = '<Browscap info nor found>'
                    self.m_renderingEngine = '<Browscap info nor found>'
                    self.m_browserVersion = '<Browscap info nor found>'
                    self.m_platformDesc = '<Browscap info nor found>'
                    self.m_devMaker = '<Browscap info nor found>'
                    self.m_devName = '<Browscap info nor found>'

                    self.m_logger.warning(self.pack_massage('No Browscap info found!'))
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

                    if not l_browscap.supports_cookies() or not l_browscap.supports_javascript():
                        self.m_badTerminal = True

        else:
            self.m_logger.warning(self.pack_massage('[NOMAIL] No User-Agent in : {0}'.format(repr(l_headers))))

        # ------------------------------------- Language ---------------------------------------------------------------
        # handles the (incorrect) case where we have "accept language" instead of "accept-language"
        if 'accept language' in self.m_headersDict.keys():
            self.m_headersDict['accept-language'] = self.m_headersDict['accept language']

        if 'accept-language' in self.m_headersDict.keys():
            l_acceptLanguage = self.m_headersDict['accept-language']
            self.m_logger.info('Accept Language  : {0}'.format(l_acceptLanguage))

            # only recognizes French. Otherwise, English
            if re.search('fr', l_acceptLanguage) is not None:
                self.m_contextDict['z'] = 'fr'
            else:
                self.m_contextDict['z'] = 'en'
        else:
            self.m_contextDict['z'] = 'en'

        # ------------------------------------- Cookies ----------------------------------------------------------------
        if 'cookie' in self.m_headersDict.keys():
            # only one cookie used, to store existing Terminal ID (if any)
            l_cookieString = str(self.m_headersDict['cookie'])
            self.m_logger.info('Raw Cookie string: {0}'.format(l_cookieString))
            self.m_reason = l_cookieString + '<br/>'

            l_cookieKey = (l_cookieString.split('=')[0]).strip()
            l_cookieValue = (l_cookieString.split('=')[1]).strip()

            if l_cookieKey != EcAppParam.gcm_sessionName:
                # this can happen if there is a version change and old cookies remain at large
                # or in case of an attempted break-in
                self.m_logger.warning(
                    self.pack_massage(
                        'Cookie found but wrong name: "{0}" Should be "{1}"'.format(
                            l_cookieKey, EcAppParam.gcm_sessionName)
                    )
                )
                # in this case, the cookie is to be destroyed, before a new one is created
                self.m_delCookie = l_cookieKey
            else:
                # the proper cookie has been found
                self.m_logger.info('Terminal ID (old): {0}'.format(l_cookieValue))
                self.m_terminalID = l_cookieValue

        # ---------------------------------- Detection of invalid browsers ---------------------------------------------
        # if the path is not one of the cases below, it cannot be good (malevolent robot or script attack)
        if not (self.path == '/' or re.match('/\?', self.path)) and \
            not re.match('/static/', self.path) and \
            not re.match('/test-error/', self.path) and \
            not re.match('/robots.txt', self.path) and \
            not re.match('/favicon.ico', self.path):

            self.m_badTerminal = True
            self.m_reason += \
                'Request for a path other than /, /?... /static/, /test-error/, /robots.txt or /favicon.ico'
        else:
            self.m_badTerminal = False

        if 'y' in self.m_contextDict.keys() and not self.m_badTerminal:
            if self.m_contextDict['y'] == 'restart':
                self.m_validatedTerminal = False
                self.m_terminalID = None
            else:
                self.m_badTerminal = (self.m_terminalID != self.m_contextDict['y'])
                self.m_reason += \
                    'Cookie Terminal ID ({0}) different from y=({1}), Cookies probably disabled'.format(
                        self.m_terminalID, self.m_contextDict['y'])
                self.m_validatedTerminal = not self.m_badTerminal

        # ------------------------------------- Previous Context -------------------------------------------------------
        # Retrieves previous context if any and cancels Terminal ID if none found
        if self.m_terminalID is not None and not self.m_badTerminal:
            self.m_logger.debug('Attempting to recover previous context')
            l_query = """
                select TX_CONTEXT, F_VALIDATED
                from TB_TERMINAL
                where TERMINAL_ID = '{0}'
                ;""".format(self.m_terminalID)

            self.m_logger.debug('l_query: {0}'.format(l_query))
            l_rowcount = None
            try:
                l_cursor = l_dbConnection.cursor(buffered=True)
                l_rowcount = -2
                l_cursor.execute(l_query)
                l_rowcount = -1
                self.m_logger.debug('Rowcount         : {0}'.format(l_cursor.rowcount))

                l_rowcount = l_cursor.rowcount
                # if no rows were found, it means that the terminal ID is absent from the table --> create a new one
                if l_cursor.rowcount == 0:
                    self.m_terminalID = None
                    self.m_validatedTerminal = False
                else:
                    # retrieve former context
                    for l_context, l_validated in l_cursor:
                        self.m_logger.info('Previous context : {0}'.format(l_context))
                        self.m_previousContext = json.loads(l_context)

                        if l_validated == 'YES':
                            # most common case: terminal already validated before
                            self.m_validatedTerminal = True
                        else:
                            # if not, the only allowed case is if this is the request triggered by the browser
                            # validation page and the terminal has been successfully validated just before
                            # in "Detection of invalid browsers" section
                            if not self.m_validatedTerminal:
                                self.m_badTerminal = True
                                self.m_reason += 'Terminal validation failed'

                l_cursor.close()
            except Exception as l_exception:
                self.m_logger.warning(self.pack_massage(
                    'Something went wrong  while retrieving ' +
                    'previous context: {0}. Rowcount: {1}'.format(repr(l_exception), l_rowcount)))
                self.m_terminalID = None
                self.m_validatedTerminal = False

        # ------------------------------------- New Terminal ID --------------------------------------------------------
        # create new terminal ID if required
        if self.m_terminalID is None or self.m_terminalID == '':
            self.m_logger.debug('Thread [{0}] before lock'.format(threading.currentThread().getName()))

            # make sure that only one thread at a time has access to this CRITICAL section
            EcRequestHandler.cm_termIDCreationLock.acquire()
            ###### START OF CRITICAL SECTION
            self.m_logger.debug('Thread [{0}] after lock'.format(threading.currentThread().getName()))

            l_created = False
            l_attemptCount = 0
            # will make 100 attempts max to create a new unique terminal ID
            while not l_created and l_attemptCount < 100:
                l_attemptCount += 1

                # the Id string is a hash of the user-agent, the ip and a random number
                l_hash = hashlib.new('MD5')
                l_hash.update(bytes(self.m_userAgent + l_clientIpPort + str(random.random()), 'utf-8'))

                self.m_terminalID = l_hash.hexdigest()
                self.m_logger.info('Terminal ID (new): {0}'.format(self.m_terminalID))

                l_query = """
                    insert into TB_TERMINAL(TERMINAL_ID, DT_CREATION, DT_LAST_UPDATE, TX_CONTEXT)
                    values('{0}', NOW(), NOW(), '{1}')
                    ;""".format(self.m_terminalID,
                                json.dumps(self.m_contextDict,
                                           ensure_ascii=False).replace("'", "''").replace("\\", "\\\\"))

                self.m_logger.debug('l_query: {0}'.format(l_query))

                # just crated so not yet validated
                self.m_validatedTerminal = False

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
                    self.m_logger.warning(self.pack_massage('Something went wrong while attempting ' +
                                          'to create Terminal ID: {0}. Error: {1} '.format(
                                              self.m_terminalID, repr(l_exception))))
                    l_created = False

            self.m_logger.debug('Thread [{0}] waiting'.format(threading.currentThread().getName()))

            ###### END OF CRITICAL SECTION
            EcRequestHandler.cm_termIDCreationLock.release()
            self.m_logger.debug('Thread [{0}] released lock'.format(threading.currentThread().getName()))

        if self.m_terminalID is None or self.m_terminalID == '':
            # abort application if no Id could be created despite all that
            self.m_logger.critical(self.pack_massage('Could not retrieve or create Terminal ID. Recovery impossible.'))
            sys.exit()

        self.m_logger.info('Terminal ID      : {0}'.format(self.m_terminalID))
        if len(self.m_terminalID) > 32:
            self.m_logger.warning(self.pack_massage('Abnormally long m_terminalID:' + self.m_terminalID))

        # ---------------------------------- Response ------------------------------------------------------------------
        if re.match('/static/', self.path):
            # fetching a static document --> rely on the base class functionality
            super().do_GET()
        elif re.match('/test-error/', self.path):
            # test trigger path to send a warning email (for e-mail setup testing purposes
            self.path = '/static/images/test.jpg'

            self.m_logger.warning(self.pack_massage('Error Email Test'))

            super().do_GET()
        elif re.match('/robots.txt', self.path):
            # redirect robots.txt fetch to the appropriate location
            self.path = '/static/robots.txt'
            super().do_GET()
        elif re.match('/favicon.ico', self.path):
            # redirect favicon fetch to the appropriate location
            self.path = '/static/images/favicon.ico'
            # PyCharm should not complain about this, self.path is an attribute of the base class Goddammit
            super().do_GET()
        elif self.path == '/' or re.match('/\?', self.path):
            if self.m_validatedTerminal:
                # validated terminal: this is where the rest of the application is called
                self.buildResponse(l_dbConnection)
            elif self.m_badTerminal:
                # the terminal does not have the required JS/cookie capabilities
                self.badBrowserMessage(l_dbConnection)
            else:
                # not necessarily bad but not yet validated
                # sends the browser test page
                self.testBrowser()
        else:
            # anything else is an error
            super().send_error(404, 'Only valid paths start with /static/')

        # -------------------------------- Log -------------------------------------------------------------------------
        l_query = """
            insert into TB_LOG(
                `TERMINAL_ID`
                , `ST_IP`
                , `N_PORT`
                , `F_BAD`
                , `TX_USER_AGENT`
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
            values(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ;"""
        # values('{0}', '{1}', {2}, '{3}', '{4}', '{5}', '{6}', '{7}', '{8}', '{9}', '{10}', '{11}', '{12}', '{13}')

        l_parameters = (
            self.m_terminalID[:32],
            self.client_address[0][:45],
            self.client_address[1],
            'Y' if self.m_badTerminal else 'N',
            self.m_userAgent,
            self.m_browser[:30],
            self.m_browserVersion[:10],
            self.m_renderingEngine[:30],
            self.m_platform[:30],
            self.m_platformDesc[:50],
            self.m_devName[:30],
            self.m_devMaker[:30],
            self.path,
            json.dumps(self.m_contextDict)
        )

        l_cursor = l_dbConnection.cursor()
        try:
            l_cursor.execute(l_query, l_parameters)
            # the cursor is executed and THEN, the connection is committed
            l_dbConnection.commit()
            l_cursor.close()
        except Exception as l_exception:
            self.m_logger.warning(self.pack_massage('Something went wrong while attempting ' +
                                  'to execute this logging query: {0} Error: {1}'.format(
                                      l_cursor.statement, repr(l_exception))))

        # ---------------------------------- Release DB connection -----------------------------------------------------

        self.m_logger.info('------------ do_Get() END ------------------------------------')
        self.m_logger.info('Handler ID       : {0}'.format(self.m_handlerID))
        self.m_logger.info('Connection ID    : {0}'.format(l_dbConnection.getID()))
        self.m_logger.info('--------------------------------------------------------------')
        EcRequestHandler.cm_connectionPool.releaseConnection(l_dbConnection)

    def badBrowserMessage(self, p_dbConnection):
        self.m_logger.info('Sending bad browser message')

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

        # since the browser is bad, delete the terminal ID (and the test terminal ID if different)
        if 'y' in self.m_contextDict.keys():
            l_testTID = self.m_contextDict['y']
        else:
            l_testTID = ''

        l_query = """
            DELETE FROM `TB_TERMINAL`
            WHERE `TERMINAL_ID` = '{0}' or `TERMINAL_ID` = '{1}'
            ;""".format(self.m_terminalID, l_testTID)

        self.m_logger.debug('l_query: {0}'.format(l_query))
        try:
            l_cursor = p_dbConnection.cursor()
            l_cursor.execute(l_query)
            # the cursor is executed and THEN, the connection is committed
            p_dbConnection.commit()
            l_cursor.close()
        except Exception as l_exception:
            self.m_logger.warning(self.pack_massage('Something went wrong while attempting ' +
                                  'to execute this query: {0} Error: {1}'.format(
                                      l_query, repr(l_exception))))

        # construct the bad browser page
        l_pageTemplate = EcTemplate(EcRequestHandler.cm_badBrowserPage)

        l_oldPath = self.path
        while re.search('&y=.*&', l_oldPath):
            l_oldPath = re.sub('&y=.*&', '&', self.path)
        while re.search('\?y=.*&', l_oldPath):
            l_oldPath = re.sub('\?y=.*&', '?', self.path)
        l_oldPath = re.sub('[&\?]y=.*$', '', l_oldPath)

        l_response = l_pageTemplate.substitute(
            LinkPrevious='.' + l_oldPath,
            NewTargetRestart=re.sub('/&y', '/?y', '.' + l_oldPath + '&y=restart'),
            BadBrowserMsg=EcAppCore.get_user_string(self.m_contextDict, 'BadBrowserMsg'),
            BadBrowserReason=self.m_reason,
            GainAccessMsg=EcAppCore.get_user_string(self.m_contextDict, 'GainAccessMsg'),
            ThisLinkMsg=EcAppCore.get_user_string(self.m_contextDict, 'ThisLinkMsg')
        )
        # In NewTarget the re.sub above is there to handle the case where the path is a bare "/"

        # In NewTargetRestart the re.sub() removes the y=xxxxx parameter (terminal ID used to test browser
        # capabilities). It handles both the case where y is at the end of several parameters (&y=) and
        # the case where y is directly located after / (/?y=)

        # and send it
        self.wfile.write(bytes(l_response, 'utf-8'))

    def testBrowser(self):
        self.m_logger.info('Testing browser capabilities')

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

        # construct the browser capabilities test page
        l_pageTemplate = EcTemplate(EcRequestHandler.cm_browserTestPage)

        l_oldPath = self.path
        while re.search('&y=.*&', l_oldPath):
            l_oldPath = re.sub('&y=.*&', '&', self.path)
        while re.search('\?y=.*&', l_oldPath):
            l_oldPath = re.sub('\?y=.*&', '?', self.path)
        l_oldPath = re.sub('[&\?]y=.*$', '', l_oldPath)

        l_response = l_pageTemplate.substitute(
            NewTarget=re.sub('/&y', '/?y', '.' + l_oldPath + '&y={0}'.format(self.m_terminalID)),
            NewTargetRestart=re.sub('/&y', '/?y', '.' + l_oldPath + '&y=restart'),
            TestingBrowserMsg=EcAppCore.get_user_string(self.m_contextDict, 'TestingBrowserMsg'),
            GainAccess1Msg=EcAppCore.get_user_string(self.m_contextDict, 'GainAccess1Msg'),
            ThisLinkMsg=EcAppCore.get_user_string(self.m_contextDict, 'ThisLinkMsg')
        )
        # In NewTarget the re.sub above is there to handle the case where the path is a bare "/"

        self.m_logger.debug('l_response: {0}'.format(l_response))

        l_bytes = bytes(l_response, 'utf-8')
        self.m_logger.debug('Bytes to send: {0}'.format(len(l_bytes)))

        # and send it
        self.wfile.write(l_bytes)

    def end_headers(self):
        # Raw request logging

        # pick a DB connection from the pool
        l_dbConnection = EcRequestHandler.cm_connectionPool.getConnection()
        l_dbConnection.debugData = 'EcRequestHandler.end_headers main working connection'

        self.m_logger.info('------------ end_headers() START ------------------------------------')
        self.m_logger.info('Handler ID       : {0}'.format(self.m_handlerID))
        self.m_logger.info('Connection ID    : {0}'.format(l_dbConnection.getID()))

        l_postData = ''
        if self.command == 'POST':
            l_length = 0
            if 'content-length' in self.m_headersDict.keys():
                l_length = int(self.m_headersDict['content-length'])

            if l_length > 0:
                l_postData = self.rfile.read(l_length)

        l_query = """
            insert into TB_RAW_LOG(
                `ST_IP`
                , `ST_PORT`
                , `ST_COMMAND`
                , `TX_USERAGENT`
                , `TX_REQUEST`
                , `TX_POST`
            )
            values('{0}', '{1}', '{2}', '{3}', '{4}', '{5}')
            ;""".format(
                self.client_address[0],
                self.client_address[1],
                self.command,
                self.m_userAgent.replace("'", "''"),
                self.requestline.replace("'", "''"),
                l_postData.replace("'", "''"))

        self.m_logger.debug('l_query: {0}'.format(l_query))
        try:
            l_cursor = l_dbConnection.cursor()
            l_cursor.execute(l_query)
            # the cursor is executed and THEN, the connection is committed
            l_dbConnection.commit()
            l_cursor.close()
        except Exception as l_exception:
            self.m_logger.warning(self.pack_massage('Something went wrong while attempting ' +
                                  'to execute this logging query: {0} Error: {1}'.format(
                                      l_query, repr(l_exception))))

        # return DB connection to the pool
        self.m_logger.info('------------ end_headers() RELEASE CONN ------------------------------')
        self.m_logger.info('Handler ID       : {0}'.format(self.m_handlerID))
        self.m_logger.info('Connection ID    : {0}'.format(l_dbConnection.getID()))
        self.m_logger.info('----------------------------------------------------------------------')

        EcRequestHandler.cm_connectionPool.releaseConnection(l_dbConnection)

        # there is something special to do here only for a GET HTTP command
        if self.command == 'GET':
            # cookie destruction if necessary
            if self.m_delCookie is not None:
                l_cookieString = '{0}=deleted; Domain={1}; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT'.format(
                    self.m_delCookie, EcAppParam.gcm_appDomain)
                self.send_header('Set-Cookie', l_cookieString)

            # send the cookie containing the terminal ID in the headers
            if self.m_terminalID is None:
                self.m_logger.warning(self.pack_massage('Terminal ID undefined - No cookie sent ({0})'.format(
                    'do_GET was called' if self.m_doGetCalled else 'do_GET was NOT called')))
            else:
                # hundred year cookie (duration in g_cookiePersistence)
                l_expire = (datetime.datetime.now(tz=pytz.utc) +
                            datetime.timedelta(EcAppParam.gcm_cookiePersistence)).strftime('%a, %d %b %Y %H:%M:%S %Z')

                l_cookieString = '{0}={1}; Domain={2}; Path=/; Expires={3}; HttpOnly'\
                    .format(EcAppParam.gcm_sessionName, self.m_terminalID, EcAppParam.gcm_appDomain, l_expire)

                self.send_header('Set-Cookie', l_cookieString)

        super().end_headers()

    def getPreviousContext(self):
        return self.m_previousContext

    def getContext(self):
        return self.m_contextDict

    def getTerminalID(self):
        return self.m_terminalID

    def getPaths(self):
        l_barePath = re.sub('[&\?]y=.*$', '', self.path)
        # the re.sub() removes the y=xxxxx parameter (terminal ID used to test browser capabilities).
        # It handles both the case where y is at the end of several parameters (&y=) and
        # the case where y is directly located after / (/?y=)

        l_noJSPath = re.sub('/&y=', '/?y=', l_barePath + '&y=bad_browser')
        # the re.sub() handles the case where y is directly located after / (/?y=)

        return l_barePath, l_noJSPath

    def buildResponse(self, p_dbConnection):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

        # get response from App
        l_response, l_newDict = EcRequestHandler.cm_appCore.getResponse(self)

        # and send it
        self.wfile.write(bytes(l_response, 'utf-8'))

        # store the final context (possibly modified by the app)

        # CORRECTION: for the moment, only the unmodified context is stored
        l_storeContext = self.m_contextDict
        l_query = """
            update TB_TERMINAL
            set
                DT_LAST_UPDATE = NOW(),
                TX_CONTEXT = '{0}',
                F_VALIDATED = 'YES'
            where TERMINAL_ID = '{1}'
            ;""".format(json.dumps(l_storeContext,
                                   ensure_ascii=False).replace("'", "''").replace("\\", "\\\\"),
                        self.m_terminalID)

        self.m_logger.debug('l_query: {0}'.format(l_query))
        try:
            l_cursor = p_dbConnection.cursor()
            l_cursor.execute(l_query)
            # the cursor is executed and THEN, the connection is committed
            p_dbConnection.commit()
            l_cursor.close()
        except Exception as l_exception:
            self.m_logger.warning(self.pack_massage('Something went wrong while storing the ' +
                                  'previous context: {0}. Error: {1}'.format(
                                      l_query, repr(l_exception))))
