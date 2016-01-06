#!/usr/bin/python3
# -*- coding: utf-8 -*-

import http.server
from socketserver import ThreadingMixIn

from ec_request_handler import *

import ec_browscap
import ec_app_core

__author__ = 'fi11222'

# ################################ SEE se3.main.py for global intro ####################################################

# required optional packages
# pytz : sudo pip3 install pytz


# Multithreaded HTTP server according to https://pymotw.com/2/BaseHTTPServer/index.html#module-BaseHTTPServer
class ThreadedHTTPServer(ThreadingMixIn, http.server.HTTPServer):
    """Handle requests in a separate thread."""

# ----------------------------------------- main() ---------------------------------------------------------------------
random.seed()

# logger init
EcLogger.logInit()

# browscap init
ec_browscap.Browscap.initBrowscap(p_skip=True)

# custom handler + app init
EcRequestHandler.initClass(
    ec_browscap.Browscap.cm_browscap,
    ec_app_core.EcAppCore('./Templates/index.html'),
    './Templates/browser_test.html')

# python http server init
l_httpd = ThreadedHTTPServer(("", g_httpPort), EcRequestHandler)

EcLogger.cm_logger.info('g_appName        : ' + g_appName)
EcLogger.cm_logger.info('g_appVersion     : ' + g_appVersion)
EcLogger.cm_logger.info('g_appTitle       : ' + g_appTitle)

EcLogger.cm_logger.info('Serving at port  : ' + str(g_httpPort))

# server main loop
l_httpd.serve_forever()
