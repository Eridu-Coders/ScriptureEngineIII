#!/usr/bin/python3
# -*- coding: utf-8 -*-

import string

from socketserver import ThreadingMixIn

from ec_request_handler import *

import ec_browscap
from se3_main import *

__author__ = 'fi11222'

# ################################ SEE se3.main.py for global intro ####################################################


# Multi-threaded HTTP server according to https://pymotw.com/2/BaseHTTPServer/index.html#module-BaseHTTPServer
class ThreadedHTTPServer(ThreadingMixIn, http.server.HTTPServer):
    """Handles requests in a separate thread each."""

# ----------------------------------------- main() ---------------------------------------------------------------------
random.seed()
EcMailer.initMailer()

# set current working dir
os.chdir(EcAppParam.gcm_appRoot)

# abort if already launched
l_countApp = 0
for l_pid in [p for p in os.listdir('/proc') if p.isdigit()]:
    try:
        l_cmd = open(os.path.join('/proc', l_pid, 'cmdline'), 'rb').read().decode()
        l_cmd = re.sub('[^{0}]'.format(string.printable), ' ', l_cmd)
        l_cmd = re.sub('\s+', ' ', l_cmd)
        if re.search('ScriptureEngineIII\.py', l_cmd) is not None \
                and re.search('python3', l_cmd) is not None:
            print('[{0}] l_cmd : <{1}>'.format(l_pid, l_cmd))
            l_countApp += 1
    except IOError:
        # process has already terminated
        continue

if l_countApp > (2 if EcAppParam.gcm_allowDoubleRunning else 1):
    print('Already Running (l_countApp = {0}) ...'.format(l_countApp))
    EcMailer.sendMail('Already Running ...', 'l_countApp = {0}'.format(l_countApp))
    sys.exit(0)

# logger init
try:
    EcLogger.logInit()
except Exception as e:
    EcMailer.sendMail('Failed to initialize EcLogger', str(e))

# Make sure MySQL is running
while True:
    try:
        EcLogger.cm_logger.debug('Attempting MySql Connection ...')
        l_connect = EcConnector(
            user=EcAppParam.gcm_dbUser, password=EcAppParam.gcm_dbPassword,
            host=EcAppParam.gcm_dbServer,
            database=EcAppParam.gcm_dbDatabase)

        l_connect.close()
        EcLogger.cm_logger.debug('MySQL ok')
        break
    except mysql.connector.Error as e:
        EcLogger.cm_logger.debug('WAITING: No MySql yet ... : ' + str(e))
        EcMailer.sendMail('WAITING: No MySql yet ...', str(e))
        time.sleep(1)
        continue


# init mysql connector class
EcConnector.classInit()

try:
    # browscap init
    ec_browscap.Browscap.initBrowscap(p_skip=EcAppParam.gcm_skipBrowscap)

    # custom handler + app init
    EcRequestHandler.initClass(
        ec_browscap.Browscap.cm_browscap,
        Se3AppCore(Se3AppParam.gcm_templateIndex),
        EcAppParam.gcm_templateBrowserTest,
        EcAppParam.gcm_templateBadBrowser)

    # python http server init
    l_httpd = ThreadedHTTPServer(("", EcAppParam.gcm_httpPort), EcRequestHandler)

    EcLogger.cm_logger.info('g_appName        : ' + EcAppParam.gcm_appName)
    EcLogger.cm_logger.info('g_appVersion     : ' + EcAppParam.gcm_appVersion)
    EcLogger.cm_logger.info('g_appTitle       : ' + EcAppParam.gcm_appTitle)

    EcLogger.cm_logger.warning('Server up and running at [{0}:{1}]'
                               .format(EcAppParam.gcm_appDomain, str(EcAppParam.gcm_httpPort)))
except Exception as e:
    EcLogger.cm_logger.critical('Cannot start server at [{0}:{1}]. Error: {2}'.format(
        EcAppParam.gcm_appDomain,
        str(EcAppParam.gcm_httpPort),
        str(e)
    ))
    sys.exit(0)

try:
    check_system_health()

    # server main loop
    l_httpd.serve_forever()
except Exception as e:
    EcLogger.cm_logger.critical('App crashed. Error: {0}'.format(str(e)))
