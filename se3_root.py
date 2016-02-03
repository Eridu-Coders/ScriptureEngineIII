# -*- coding: utf-8 -*-

from se3_word import *

__author__ = 'fi11222'

# -------------------------- Logger ------------------------------------------------------------------------------------
g_loggerRoot = logging.getLogger(ec_app_params.g_appName + '.root')
if ec_app_params.g_verboseModeOn:
    g_loggerRoot.setLevel(logging.INFO)
if ec_app_params.g_debugModeOn:
    g_loggerRoot.setLevel(logging.DEBUG)


# -------------------------- Root Response -----------------------------------------------------------------------------
def get_root(p_previousContext, p_context, p_dbConnectionPool):
    g_loggerRoot.info('Getting root response')
    g_loggerRoot.debug('p_previousContext: {0}'.format(p_previousContext))
    g_loggerRoot.debug('p_context: {0}'.format(p_context))

    # ---------------------- Parameter check ---------------------------------------------------------------------------
    l_response = root_control(p_context)

    if len(l_response) > 0:
        return l_response, p_context, 'Error'

    l_dbConnection = p_dbConnectionPool.getConnection()

    # split components of the root id field
    l_rootIdList = p_context['d'].split('|')

    # window title
    l_title = ec_app_params.g_appTitle

    if len(l_rootIdList) == 1:
        l_oneRootId = l_rootIdList[0]
    else:
        l_oneRootId = None

    l_rootSelector = '"' + '","'.join(l_rootIdList) + '"'
    l_rootCountDict = dict((l_rootId, 0) for l_rootId in l_rootIdList)

    # list of root info
    l_query = """
        select
            ST_GROUND
            , ST_TRANSLIT
            , ID_GROUP_0
            , TX_DEF
            , ID_ROOT
        from
            TB_ROOT
        where
            ID_ROOT in ({0})
        order by
            ID_ROOT
        ;""".format(l_rootSelector)

    g_loggerRoot.debug('l_query {0}'.format(l_query))
    try:
        l_cursor = l_dbConnection.cursor(buffered=True)
        l_cursor.execute(l_query)

        if l_cursor.rowcount == 0:
            return get_user_string(p_context, 'e_noRoot').format(p_context['d']), p_context, 'Error'
        else:
            # response start
            l_response = '<table id="rOuterTable">'

            l_rootsCell = '<tr><td class="rRootsCell" colspan="4">\n'
            for l_ground, l_translit, l_idGroup0, l_def, l_idRootByte in l_cursor:

                l_idRoot = l_idRootByte.decode('utf-8') if l_idRootByte is not None else None

                # window title
                l_title = l_ground + '-' + l_title

                # ground text style based on book collection
                l_groundStyle = 'rGroundHebrew'
                if l_idGroup0 == 'NT':
                    l_groundStyle = 'rGroundGreek'
                elif l_idGroup0 == 'FT':
                    l_groundStyle = 'rGroundArabic'

                if len(l_def.strip()) > 0:
                    l_defCell = '<tr><td>‟{0}”</td></tr>'.format(l_def)
                else:
                    l_defCell = ''

                l_rootsCell += ('<table class="rOneRoot">' +
                                '<tr><td class="{0}">{1}</td></tr>' +
                                '<tr><td class="rTranslit">{2}</td></tr>' +
                                l_defCell +
                                '<tr><td class="rRootCount">{4}</td></tr>' +
                                '</table>\n').format(
                    l_groundStyle, l_ground, l_translit, l_def, '__{0}-Count__'.format(sanitize_for_re(l_idRoot)))
                #        {0}          {1}        {2}      {3}       {4}

            l_rootsCell += '</td></tr>\n'
            l_response += l_rootsCell

        l_cursor.close()
    except Exception as l_exception:
        g_loggerRoot.warning('Something went wrong {0}'.format(l_exception.args))

    # -------------------- Homonymous Roots (if any) -------------------------------------------------------------------
    if l_oneRootId is not None:
        l_query = """
            select
                R.ST_GROUND
                , R.ID_GROUP_0
                , R.TX_DEF
                , R.ID_ROOT
            from
                TB_ROOT R join TB_ROOT_ROOT L on R.ID_ROOT = L.ID_ROOT2
            where
                L.ID_ROOT1 = '{0}'
            order by
                ID_ROOT
            ;""".format(l_oneRootId)

        g_loggerRoot.debug('l_query {0}'.format(l_query))
        try:
            l_cursor = l_dbConnection.cursor(buffered=True)
            l_cursor.execute(l_query)

            if l_cursor.rowcount > 0:
                l_response += ('<tr><td class="rOtherRootsCell" colspan="4">' +
                               '<span class="pFieldName">{0}:</span> \n').format(
                    get_user_string(p_context, 'w_homonymousRoot') if l_cursor.rowcount == 1
                    else get_user_string(p_context, 'w_homonymousRoots')
                )

                l_allRoots = l_oneRootId
                for l_ground, l_idGroup0, l_def, l_idRootByte in l_cursor:
                    l_idRoot = l_idRootByte.decode('utf-8')

                    l_allRoots += '|{0}'.format(l_idRoot)

                    # ground text style based on book collection
                    l_groundStyle = 'rGroundHebrew'
                    if l_idGroup0 == 'NT':
                        l_groundStyle = 'rGroundGreek'
                    elif l_idGroup0 == 'FT':
                        l_groundStyle = 'rGroundArabic'

                    l_rootLink = makeLinkCommon(p_context, '', '', '',
                                                '<span class="{0}">{1}</span>'.format(l_groundStyle, l_ground),
                                                p_command='R',
                                                p_class='RootLink',
                                                p_wordId=l_idRoot)

                    l_response += l_rootLink + (' ({0})'.format(l_def) if len(l_def.strip()) > 0 else '') + ' '

                l_all = makeLinkCommon(p_context, '', '', '',
                                       get_user_string(p_context, 'w_allRoots'),
                                       p_command='R',
                                       p_class='RootLink',
                                       p_wordId=l_allRoots)

                l_response += l_all + '</td></tr>\n'

            l_cursor.close()
        except Exception as l_exception:
            g_loggerRoot.warning('Something went wrong {0}'.format(l_exception.args))

    # -------------------- List of Occurences --------------------------------------------------------------------------
    # list of lexicon entries linked to root(s)
    l_query = """
        select
            L.ST_GROUND
            , L.ST_TRANSLIT
            , L.ST_TYPE
            , L.TX_DEF_SHORT
            , L.ID_STRONGS
            , F.ID_ROOT
        from
            TB_ROOT_FORM F join TB_LEXICON L on F.ID_STRONGS = L.ID_STRONGS
        where
            F.ID_ROOT in ({0})
        order by
            L.ID_STRONGS
        ;""".format(l_rootSelector)

    g_loggerRoot.debug('l_query {0}'.format(l_query))
    try:
        l_cursor = l_dbConnection.cursor(buffered=True)
        l_cursor.execute(l_query)

        for l_ground, l_translit, l_type, l_def, l_idStrongs,  l_idRootByte in l_cursor:
            l_idRoot = l_idRootByte.decode('utf-8')

            # ground text style based on Strong's ID initial
            l_groundStyle = 'rGroundHebrew'
            if l_idStrongs[0:1] == 'G':
                l_groundStyle = 'rGroundGreek'
            elif l_idStrongs[0:1] == 'A':
                l_groundStyle = 'rGroundArabic'

            l_occuVersion, l_occuCount, l_occuString = getOccurences(p_context, l_dbConnection, l_idStrongs)

            l_rootCountDict[l_idRoot] += l_occuCount

            g_loggerRoot.debug('l_rootCount[{0}]: {1}'.format(l_idRoot, l_rootCountDict[l_idRoot]))
            if l_occuCount > 0:
                # top title box with gray background
                l_response += ('<tr><td colspan="4" class="wOccurencesTitle">' +
                               '<span class="{0}">{1}</span> ' +
                               '<span class="wTranslit">{2}</span> ' +
                               ('‟{0}” '.format(l_def) if len(l_def.strip()) > 0 else '') +
                               ('({0}) '.format(l_type) if len(l_type.strip()) > 0 else '') +
                               '– {5} {3}{4}' +
                               '</td></tr>\n').format(
                    l_groundStyle, l_ground, l_translit,
                    get_user_string(p_context, 'w_OccurencesTitle'), l_occuVersion, l_occuCount
                )

                l_response += l_occuString

        l_cursor.close()
    except Exception as l_exception:
        g_loggerRoot.warning('Something went wrong {0}'.format(l_exception.args))

    for l_rootId, l_count in l_rootCountDict.items():
        l_response = re.sub('__' + sanitize_for_re(l_rootId) + '-Count__',
                            str(l_count) + ' ' + get_user_string(p_context, 'w_OccurencesTitle'),
                            l_response)

    # -------------------- End -----------------------------------------------------------------------------------------
    l_response += '</table>'

    p_dbConnectionPool.releaseConnection(l_dbConnection)

    return l_response, p_context, l_title


# helper function replacing characters which would interfere with re matching
def sanitize_for_re(p_string):
    l_string = re.sub(r'\*', '⅓', p_string)
    l_string = re.sub(r'\$', '⅔', l_string)
    l_string = re.sub(r'\{', '⅛', l_string)
    l_string = re.sub(r'\}', '⅜', l_string)
    l_string = re.sub(r'\^', '⅝', l_string)
    l_string = re.sub(r'\(', '⅞', l_string)
    l_string = re.sub(r'\)', 'ↄ', l_string)
    l_string = re.sub(r'\.', '←', l_string)
    l_string = re.sub(r'\+', '↑', l_string)
    l_string = re.sub(r'\[', '→', l_string)
    l_string = re.sub(r'\]', '↓', l_string)
    l_string = re.sub(r'\?', '↔', l_string)
    l_string = re.sub(r',', '↕', l_string)
    l_string = re.sub(r'\|', '↨', l_string)

    return l_string
