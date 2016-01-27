# -*- coding: utf-8 -*-

from se3_utilities import *

__author__ = 'fi11222'

# -------------------------- Logger ------------------------------------------------------------------------------------
g_loggerLexicon = logging.getLogger(ec_app_params.g_appName + '.lexicon')
if ec_app_params.g_verboseModeOn:
    g_loggerLexicon.setLevel(logging.INFO)
if ec_app_params.g_debugModeOn:
    g_loggerLexicon.setLevel(logging.DEBUG)

# -------------------------- Logger ------------------------------------------------------------------------------------
# Arabic alphabet : useless but nice
g_alphabet = 'أ ب ت ث ج ح خ د ذ ر ز س ش ص ض ط ظ ع غ ف ق ك ل م ن ه و ي'


# Arabic lexicon
def lexicon_arabic(p_previousContext, p_context, p_dbConnectionPool):

    l_dbConnection = p_dbConnectionPool.getConnection()

    # Page structure : an outer div with an inner floating table (display: inline-block)
    # with 2 columns
    # each column contain inline-block tables for each letter of the Arabic alphabet
    l_response = '<div class="LexOuter">\n<table class="LexInner"><tr><td class="LexLeft">\n'

    # All Arabic roots in alphabetical order
    l_query = """
        SELECT
            ST_GROUND
            , ST_TRANSLIT
            , ID_ROOT
        FROM  TB_ROOT
        WHERE  ID_GROUP_0 =  'FT'
        ORDER BY ST_GROUND;"""

    try:
        l_cursor = l_dbConnection.cursor(buffered=True)
        l_cursor.execute(l_query)

        l_curInitial = ''
        l_letterCount = 0
        for l_ground, l_translit, l_idRoot in l_cursor:
            if l_curInitial != l_ground[0]:
                # letter break
                if l_curInitial != '':
                    # if it is not the first one --> end of table and br so that the next table will be
                    # underneath it. Otherwise, since the tables are inline-block, the next one will be to the right
                    l_response += '</table><br/>'

                g_loggerLexicon.debug('l_letterCount {0}'.format(l_letterCount))
                if l_letterCount == 15:
                    # column break at 15th letter: this is closest to 1/2
                    l_response += '</td><td class="LexRight">\n'

                l_letterCount += 1

                # begin new table
                l_response += '<table class="ArabLex">\n' + \
                              '<tr><td colspan="2" class="LexLetter">{0}</td></tr>\n'.format(l_ground[0])
                l_curInitial = l_ground[0]

            # Link to root
            l_rootLink = '<a href="" class="GoRoot" p_idroot="{1}">{0}</a>'.format(l_ground, l_idRoot.decode('utf-8'))

            # left cell --> root
            l_response += '<tr><td class="LexGround">{0}</td>\n'.format(l_rootLink)
            # right cell --> translit
            l_response += '<td class="LexTranslit">{0}</td></tr>\n'.format(l_translit)

        l_cursor.close()
    except Exception as l_exception:
        g_loggerLexicon.warning('Something went wrong {0}'.format(l_exception.args))

    # end
    l_response += '</table></td></tr></table></div>\n'

    p_dbConnectionPool.releaseConnection(l_dbConnection)

    return l_response, p_context, ec_app_params.g_appTitle


# hebrew lexicon : same principle
# except that here there are some translations in addition to transliterations
def lexicon_hebrew(p_previousContext, p_context, p_dbConnectionPool):
    l_dbConnection = p_dbConnectionPool.getConnection()

    l_response = '<div class="LexOuter">\n<table class="LexInner"><tr><td class="LexLeft">\n'

    l_query = """
        SELECT
            ST_GROUND
            , ST_TRANSLIT
            , ID_ROOT
            , TX_DEF
        FROM  TB_ROOT
        WHERE  ID_GROUP_0 =  'OT'
        ORDER BY ST_GROUND;"""

    try:
        l_cursor = l_dbConnection.cursor(buffered=True)
        l_cursor.execute(l_query)

        l_curInitial = ''
        l_letterCount = 0
        for l_ground, l_translit, l_idRoot, l_def in l_cursor:
            if l_curInitial != l_ground[0]:
                if l_curInitial != '':
                    l_response += '</table><br/>'

                g_loggerLexicon.debug('l_letterCount {0}'.format(l_letterCount))
                if l_letterCount == 12:
                    l_response += '</td><td class="LexRight">\n'

                l_letterCount += 1

                l_response += '<table class="HebrewLex">\n' + \
                              '<tr><td colspan="2" class="LexLetter">{0}</td></tr>\n'.format(l_ground[0])
                l_curInitial = l_ground[0]

            l_rootLink = '<a href="" class="GoRoot" p_idroot="{1}">{0}</a>'.format(l_ground, l_idRoot.decode('utf-8'))

            # first cell --> root
            l_response += '<tr><td class="LexGround">{0}</td>\n'.format(l_rootLink)
            # second cell --> transliteration
            l_response += '<td class="LexTranslit">{0}</td>\n'.format(l_translit)
            # third cell --> translation
            l_response += '<td class="LexDef">{0}</td></tr>\n'.format(l_def)

        l_cursor.close()
    except Exception as l_exception:
        g_loggerLexicon.warning('Something went wrong {0}'.format(l_exception.args))

    l_response += '</table></td></tr></table></div>\n'

    p_dbConnectionPool.releaseConnection(l_dbConnection)

    return l_response, p_context, ec_app_params.g_appTitle

# greek letter dictionary to remove diacritics
g_greekLetterTranslate = {
    'Α': 'Α',
    'Β': 'Β',
    'Γ': 'Γ',
    'Δ': 'Δ',
    'Ε': 'Ε',
    'Ζ': 'Ζ',
    'Η': 'Η',
    'Θ': 'Θ',
    'Ι': 'Ι',
    'Κ': 'Κ',
    'Λ': 'Λ',
    'Μ': 'Μ',
    'Ν': 'Ν',
    'Ξ': 'Ξ',
    'Ο': 'Ο',
    'Π': 'Π',
    'Ρ': 'Ρ',
    'Σ': 'Σ',
    'Τ': 'Τ',
    'Υ': 'Υ',
    'Φ': 'Φ',
    'Χ': 'Χ',
    'Ψ': 'Ψ',
    'Ω': 'Ω',
    'α': 'Α',
    'β': 'Β',
    'γ': 'Γ',
    'δ': 'Δ',
    'ε': 'Ε',
    'ζ': 'Ζ',
    'η': 'Η',
    'θ': 'Θ',
    'ι': 'Ι',
    'κ': 'Κ',
    'λ': 'Λ',
    'μ': 'Μ',
    'ν': 'Ν',
    'ξ': 'Ξ',
    'ο': 'Ο',
    'π': 'Π',
    'ς': 'Σ',
    'σ': 'Σ',
    'τ': 'Τ',
    'υ': 'Υ',
    'φ': 'Φ',
    'χ': 'Χ',
    'ψ': 'Ψ',
    'ω': 'Ω',
    'ἀ': 'Α',
    'ἁ': 'Α',
    'ἄ': 'Α',
    'ἅ': 'Α',
    'ἆ': 'Α',
    'Ἀ': 'Α',
    'Ἁ': 'Α',
    'Ἄ': 'Α',
    'Ἆ': 'Α',
    'ἐ': 'Ε',
    'ἑ': 'Ε',
    'ἔ': 'Ε',
    'ἕ': 'Ε',
    'Ἐ': 'Ε',
    'Ἑ': 'Ε',
    'Ἔ': 'Ε',
    'Ἕ': 'Ε',
    'ἠ': 'Η',
    'ἡ': 'Η',
    'ἤ': 'Η',
    'ἥ': 'Η',
    'ἦ': 'Η',
    'ἧ': 'Η',
    'Ἠ': 'Η',
    'Ἡ': 'Η',
    'Ἤ': 'Η',
    'ἰ': 'Ι',
    'ἱ': 'Ι',
    'ἴ': 'Ι',
    'ἵ': 'Ι',
    'ἶ': 'Ι',
    'Ἰ': 'Ι',
    'Ἱ': 'Ι',
    'ὀ': 'Ο',
    'ὁ': 'Ο',
    'ὄ': 'Ο',
    'ὅ': 'Ο',
    'Ὀ': 'Ο',
    'ὑ': 'Υ',
    'ὕ': 'Υ',
    'ὗ': 'Υ',
    'Ὑ': 'Υ',
    'ὠ': 'Ω',
    'ὡ': 'Ω',
    'ὤ': 'Ω',
    'ὥ': 'Ω',
    'ὦ': 'Ω',
    'ὧ': 'Ω',
    'Ὡ': 'Ω',
    'ᾄ': 'Α',
    'ᾅ': 'Α',
    'ᾠ': 'Ω',
    'ῥ': 'Ρ',
    'Ῥ': 'Ρ'
}


# greek lexicon
# same general principle except that here there are no roots and that the lexicon entries are therefore words
def lexicon_greek(p_previousContext, p_context, p_dbConnectionPool):
    l_dbConnection = p_dbConnectionPool.getConnection()

    l_response = '<div class="LexOuter">\n<table class="LexInner"><tr><td class="LexLeft">\n'

    l_query = """
        SELECT
            ST_GROUND
            , ST_TRANSLIT
            , ID_STRONGS
            , TX_DEF_SHORT
            FROM TB_LEXICON
            WHERE
                ID_GROUP_0 = 'NT'
                AND LENGTH( TRIM( ST_GROUND ) ) > 0
            ORDER BY ST_GROUND"""

    try:
        l_cursor = l_dbConnection.cursor(buffered=True)
        l_cursor.execute(l_query)

        l_curInitial = ''
        l_letterCount = 0
        for l_ground, l_translit, l_idStrongs, l_def in l_cursor:

            # diacritics removal
            l_firstGround = g_greekLetterTranslate[l_ground[0]]

            if l_curInitial != l_firstGround:
                if l_curInitial != '':
                    l_response += '</table><br/>'

                g_loggerLexicon.debug('l_letterCount {0}'.format(l_letterCount))
                if l_letterCount == 12:
                    l_response += '</td><td class="LexRight">\n'

                l_letterCount += 1

                l_response += '<table class="GreekLex">\n' + \
                              '<tr><td colspan="2" class="LexLetter">{0}</td></tr>\n'.format(l_firstGround)
                l_curInitial = l_firstGround

            l_wordLink = '<a href="" class="GoWord" wordid="_-_-{1}">{0}</a>'.format(l_ground, l_idStrongs)

            # first cell --> word
            l_response += '<tr><td class="LexGround">{0}</td>\n'.format(l_wordLink)
            # second cell --> transliteration
            l_response += '<td class="LexTranslit">{0}</td>\n'.format(l_translit)
            # third cell --> translation
            l_response += '<td class="LexDef">{0}</td></tr>\n'.format(l_def)

        l_cursor.close()
    except Exception as l_exception:
        g_loggerLexicon.warning('Something went wrong {0}'.format(l_exception.args))

    l_response += '</table></td></tr></table></div>\n'

    p_dbConnectionPool.releaseConnection(l_dbConnection)

    return l_response, p_context, ec_app_params.g_appTitle
