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
        
        # Add a record to TB_MSG, thus testing the db connection
        l_conn = self.m_connectionPool.getConnection()
        l_conn.debugData = 'EcAppCore.__init__ recording start in TB_MSG'
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
                '__init__',
                0,
                '{0} v. {1} starting'.format(
                    EcAppParam.gcm_appName,
                    EcAppParam.gcm_appVersion
                )
            ))
            l_conn.commit()
        except Exception as e:
            g_loggerAppCore.warning('TB_MSG insert failure: {0}-{1}'.format(
                type(e).__name__,
                repr(e)
            ))
            raise

        l_cursor.close()
        self.m_connectionPool.releaseConnection(l_conn)
        g_loggerAppCore.info('Sucessuful TB_MSG insert - The DB appears to be working')


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
