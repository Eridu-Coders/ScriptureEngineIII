# -*- coding: utf-8 -*-

from ec_utilities import *
__author__ = 'fi11222'

g_loggerAppCore = logging.getLogger(EcAppParam.gcm_appName + '.appCore')
if EcAppParam.gcm_verboseModeOn:
    g_loggerAppCore.setLevel(logging.INFO)
if EcAppParam.gcm_debugModeOn:
    g_loggerAppCore.setLevel(logging.DEBUG)


class EcAppCore(EcAppParam):
    def __init__(self, p_templatePath):
        # connecion pool init
        self.m_connectionPool = EcConnectionPool()

    # connecion pool access
    def getConnectionPool(self):
        return self.m_connectionPool

    #def getResponse(self, p_previousContext, p_context, p_dbConnectionPool, p_urlPath, p_noJSPath, p_terminalID):
    #    pass
    def getResponse(self, p_requestHandler):
        pass

    # ------------------------- Access to i18n strings -----------------------------------------------------------------
    @staticmethod
    def get_user_string(p_context, p_stringId):
        # p_context['z'] = UI language
        # g_userStrings = dict of strings defined in ec_app_params.py.
        return EcAppParam.i18n(p_context['z'] + '-' + p_stringId)
