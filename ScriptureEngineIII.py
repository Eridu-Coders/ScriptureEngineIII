#!/usr/bin/python3
# -*- coding: utf-8 -*-

import http.server
import os
import string

from socketserver import ThreadingMixIn

from ec_request_handler import *

import ec_browscap
import ec_app_core

__author__ = 'fi11222'

# ################################ SEE se3.main.py for global intro ####################################################


# Multithreaded HTTP server according to https://pymotw.com/2/BaseHTTPServer/index.html#module-BaseHTTPServer
class ThreadedHTTPServer(ThreadingMixIn, http.server.HTTPServer):
    """Handle requests in a separate thread."""

# ----------------------------------------- main() ---------------------------------------------------------------------
random.seed()

# set current working dir
os.chdir(g_appRoot)

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
        # print('l_cmd : ' + l_cmd)
    except IOError:
        # process has already terminated
        continue

if l_countApp > 1:
    print('Already Running ...')
    sys.exit(0)

# Make sure MySQL is running
while True:
    try:
        # mysql.connector.connect(
        l_connect = EcConnector(
            user=g_dbUser, password=g_dbPassword,
            host=g_dbServer,
            database=g_dbDatabase)

        l_connect.close()
        print('MySQL ok')
        break
    except mysql.connector.Error:
        continue

try:
    # logger init
    EcLogger.logInit()
except Exception as e:
    sendMail('Failed to initialize EcLogger', str(e))

try:
    # browscap init
    ec_browscap.Browscap.initBrowscap(p_skip=g_skipBrowscap)

    # custom handler + app init
    EcRequestHandler.initClass(
        ec_browscap.Browscap.cm_browscap,
        ec_app_core.EcAppCore(g_templateIndex),
        g_templateBrowser,
        g_templateBad)

    # python http server init
    l_httpd = ThreadedHTTPServer(("", g_httpPort), EcRequestHandler)

    EcLogger.cm_logger.info('g_appName        : ' + g_appName)
    EcLogger.cm_logger.info('g_appVersion     : ' + g_appVersion)
    EcLogger.cm_logger.info('g_appTitle       : ' + g_appTitle)

    EcLogger.cm_logger.warning('Server up and running at [{0}:{1}]'.format(g_appDomain, str(g_httpPort)))
except Exception as e:
    EcLogger.cm_logger.critical('Cannot start server at [{0}:{1}]. Error: {2}'.format(
        g_appDomain,
        str(g_httpPort),
        str(e)
    ))
    sys.exit(0)

try:
    # server main loop
    l_httpd.serve_forever()
except Exception as e:
    EcLogger.cm_logger.critical('App crashed. Error: {2}'.format(str(e)))
