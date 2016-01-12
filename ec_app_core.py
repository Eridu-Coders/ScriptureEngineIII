# -*- coding: utf-8 -*-

import logging

from ec_app_params import *
import se3_main

__author__ = 'fi11222'

g_loggerAppCore = logging.getLogger(g_appName + '.appCore')
if g_verboseModeOn:
    g_loggerAppCore.setLevel(logging.INFO)
if g_debugModeOn:
    g_loggerAppCore.setLevel(logging.DEBUG)


class EcAppCore:
    def __init__(self, p_templatePath):
        se3_main.init(p_templatePath)

    @staticmethod
    def getResponse(p_previousContext, p_context, p_dbConnectionPool, p_urlPath, p_noJSPath):
        g_loggerAppCore.info('Getting response from App Core')

        return se3_main.se3_entryPoint(p_previousContext, p_context, p_dbConnectionPool, p_urlPath, p_noJSPath)
