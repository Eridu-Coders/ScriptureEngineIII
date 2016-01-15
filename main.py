#!/usr/bin/python3
# -*- coding: utf-8 -*-

import http.server
import smtplib

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
ec_browscap.Browscap.initBrowscap(p_skip=g_skipBrowscap)

# custom handler + app init
EcRequestHandler.initClass(
    ec_browscap.Browscap.cm_browscap,
    ec_app_core.EcAppCore('./Templates/index.html'),
    './Templates/browser_test.html',
    './Templates/bad_browser.html')

# python http server init
l_httpd = ThreadedHTTPServer(("", g_httpPort), EcRequestHandler)

EcLogger.cm_logger.info('g_appName        : ' + g_appName)
EcLogger.cm_logger.info('g_appVersion     : ' + g_appVersion)
EcLogger.cm_logger.info('g_appTitle       : ' + g_appTitle)

EcLogger.cm_logger.info('Serving at port  : ' + str(g_httpPort))

sender = g_mailSender
receivers = g_mailRecipients

message = """From: {0}
To: {1}
Subject: SMTP e-mail test

This is a test e-mail message.
""".format(g_mailSender, g_mailRecipients[0])

try:
   smtpObj = smtplib.SMTP('smtp.free.fr')
   smtpObj.sendmail(sender, receivers, message)
   print("Successfully sent email")
except smtplib.SMTPException:
   print("Error: unable to send email")

# server main loop
l_httpd.serve_forever()
