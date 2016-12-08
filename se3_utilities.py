# -*- coding: utf-8 -*-

import html
import logging
import re

from ec_app_params import *

__author__ = 'fi11222'

# ------------------------- Response building class --------------------------------------------------------------------
class Se3ResponseBuilder:
    def __init__(self, p_app, p_requestHandler, p_context):
        self.m_logger = logging.getLogger(EcAppParam.gcm_appName + '.Se3ResponseBuilder')
        if EcAppParam.gcm_verboseModeOn:
            self.m_logger.setLevel(logging.INFO)
        if EcAppParam.gcm_debugModeOn:
            self.m_logger.setLevel(logging.DEBUG)
        self.m_logger.info('+++ Se3ResponseBuilder created')

        self.m_app = p_app
        self.m_requestHandler = p_requestHandler

        self.m_context = p_context
        self.m_previousContext = self.m_requestHandler.getPreviousContext()


    # default build response: does nothing
    def buildResponse(self):
        l_response, l_context, l_title = '', self.m_context, ''
        return l_response, l_context, l_title

    # ------------------------- One verse translation display --------------------------------------------------------------
    # Common verse formatting for search output and passages
    # p_rightToLeft: for Hebrew and Arabic
    # p_highlightList: list of words to highlight (search output only)
    # p_highlightCaseSensitive: highlight take case into account ? (search output only)
    # p_counter: number to display btw [] to the left of the verse ref (search output only)
    def makeVerse(self, p_bookId, p_chapterNumber, p_verseNumber, p_verseText, p_bookShort, p_rightToLeft=False,
                  p_highlightList=None, p_highlightCaseSensitive=False, p_counter=None, p_versionLabel=None):

        l_verseText = p_verseText

        l_verseText = html.unescape(l_verseText)

        # in order for highlighting to work properly, the words must have been ordered LONGEST FIRST so that the
        # 'willingly unwillingly problem does not arise'. This is done when processing the search parameters
        if p_highlightList is not None:
            for l_word in p_highlightList:
                l_word = self.clean_search_word(l_word)
                l_verseText = re.sub(
                    '(' + l_word + ')',
                    r'<b>\1</b>',
                    l_verseText,
                    flags=re.IGNORECASE if not p_highlightCaseSensitive else 0)

        # proper class, depending on language
        if self.is_Hebrew(l_verseText):
            l_verseText = '<span class="sHebrew">{0}</span>'.format(l_verseText)
        elif self.is_Greek(l_verseText):
            l_verseText = '<span class="sGreek">{0}</span>'.format(l_verseText)
        elif self.is_Arabic(l_verseText):
            self.l_verseText = '<span class="sArabic">{0}</span>'.format(l_verseText)

        self.m_logger.debug('l_verseText: {0}'.format(l_verseText))

        l_jumpLink = self.makeLinkCommon(p_bookId, p_chapterNumber, p_verseNumber,
                                    '{0} {1}:{2}'.format(p_bookShort, p_chapterNumber, p_verseNumber))

        if p_rightToLeft:
            # for right to left text (Arabic & Hebrew), the verse reference is put into a <div> that the CSS floats
            # rightwards. That way, the text floats around it as it should
            return ('<div class="sFloatingVerse">{1}' + l_jumpLink +
                    (' <span class="sCounter">[{0}]</span>'.format(p_counter) if p_counter is not None else '') +
                    '</div>' +
                    '<p class="OneVerseTranslationRL">{0}</p>').format(
                        l_verseText,
                        ' <span class="sCounter">[{0}]</span>'.format(p_versionLabel) if p_versionLabel is not None else ''
                    )
        else:
            # for left to right text (translations & Greek)
            return ('<p class="OneVerseTranslation">' +
                    ('<span class="sCounter">[{0}]</span> '.format(p_counter) if p_counter is not None else '') +
                    l_jumpLink +
                    ' <span class="TranslationText">{0}</span>{1}</p>').format(
                        l_verseText,
                        ' <span class="sCounter">[{0}]</span>'.format(p_versionLabel) if p_versionLabel is not None else ''
                    )
        # In both cases, the verse reference is put into a link containing a ref with the full context.
        # This allows the link to be opened in another window or browser tab

    # common entry point to make left-click friendly links
    def makeLinkCommon(self, p_bookId, p_chapterNumber, p_verseNumber, p_label,
                       p_command='V', p_class='VerseLink', p_wordId=None, p_toolTip=None, p_v2=None):

        l_newContext = self.m_context.copy()
        l_newContext['K'] = p_command
        l_newContext['b'] = p_bookId
        l_newContext['c'] = p_chapterNumber
        l_newContext['v'] = p_verseNumber

        if p_wordId is not None:
            l_newContext['d'] = p_wordId

        if p_v2 is not None:
            l_newContext['w'] = p_v2

        l_link = self.makeLink(
            l_newContext,
            p_class,
            p_label,
            p_toolTip)

        return l_link

    # Create a link to a new context
    def makeLink(self, p_context, p_class, p_label, p_toolTip=None):
        if p_toolTip is None:
            l_link = '<a class="{0}" href="./?'.format(p_class)
        else:
            l_link = '<a class="{0}" title="{1}" href="./?'.format(p_class, p_toolTip)

        l_listParam = ['K', 'b', 'c', 'd', 'e', 'h', 'i', 'j', 'l', 'o', 'p', 'q', 's', 't', 'u', 'v', 'w']

        l_link += '&'.join(['{0}={1}'.format(p, p_context[p]) for p in l_listParam])

        l_link += '">{0}</a>'.format(p_label)

        return l_link

    # Word cleanup before use in search query --------------------------------------------------------------------------
    # If a word is in a given ancient language (Hebrew, Arabic or Greek), remove all characters not of this language
    def clean_search_word(self, p_word):
        if self.is_Greek(p_word):
            # Greek [\u0370-\u03FF\u1F00-\u1FFF]
            return re.sub('[^\u0370-\u03FF\u1F00-\u1FFF]', '', p_word)
        elif self.is_Hebrew(p_word):
            # Hebrew [\u0590-\u05FF\u200D]
            return re.sub('[^\u0590-\u05FF\u200D]', '', p_word)
        elif self.is_Arabic(p_word):
            # Arabic [\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]
            return re.sub('[^\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]', '', p_word)
        else:
            return re.sub('[^ a-zA-Zéèêàâôïäëçùûʼ]', '', p_word)

    def is_Greek(self, p_word):
        return re.search('[\u0370-\u03FF\u1F00-\u1FFF]', p_word) is not None

    def is_Hebrew(self, p_word):
        return re.search('[\u0590-\u05FF\u200D]', p_word) is not None

    def is_Arabic(self, p_word):
        return re.search('[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]', p_word) is not None

    # Neighborhood creation function -----------------------------------------------------------------------------------
    # This function is never used online (it used to be but was too slow)
    # Instead, the neighborhoods are created (by this function) using the off-line script makeNeighborhoods.py
    # which stores them into the TB_INTERLINEAR table.
    @staticmethod
    def getNeighborhood(p_dbConnectionPool, p_interlinear, p_bookId, p_chapter, p_verse, p_wordStart, p_wordEnd, p_word):
        # p_word is used to highlight the word at the center of the neighborhood

        l_logger = logging.getLogger(EcAppParam.gcm_appName + '.Se3ResponseBuilder-getNeighborhood')
        if EcAppParam.gcm_verboseModeOn:
            l_logger.setLevel(logging.INFO)
        if EcAppParam.gcm_debugModeOn:
            l_logger.setLevel(logging.DEBUG)

        l_query = """
            select TX_TRANSLATION, N_WORD
            from TB_INTERLINEAR
            where
                ID_INTERL = '{0}'
                and ID_BOOK = '{1}'
                and N_CHAPTER = {2}
                and N_VERSE = {3}
                and N_WORD >= {4}
                and N_WORD <= {5}
            order by
                N_WORD
        ;""".format(p_interlinear, p_bookId, p_chapter, p_verse, p_wordStart, p_wordEnd)

        l_connector = p_dbConnectionPool.getConnection()
        l_connector.debugData = 'Se3ResponseBuilder.getNeighborhood main working connection'

        l_neighborhood = ''
        l_logger.info('l_query {0}'.format(l_query))
        try:
            l_cursor = l_connector.cursor(buffered=True)
            l_cursor.execute(l_query)

            for l_text, l_word in l_cursor:
                if p_interlinear == 'L':
                    # text cleanup if LXX (not really necessary now ...)
                    l_text = re.sub('<[^>]+>', '', l_text)
                    l_text = re.sub('[0-9]', '', l_text)
                    l_text = re.sub('[][]', '', l_text)
                    l_text = re.sub('\s+', ' ', l_text).strip()

                # neighborhood words are separated by |
                if l_word == p_word:
                    l_neighborhood += '&nbsp;| <b>{0}</b>'.format(l_text)
                else:
                    l_neighborhood += '&nbsp;| {0}'.format(l_text)

            l_neighborhood = re.sub('\s+', ' ', l_neighborhood).strip()[8:]

            l_cursor.close()
        except Exception as l_exception:
            l_logger.warning('Something went wrong {0}'.format(l_exception.args))

        p_dbConnectionPool.releaseConnection(l_connector)

        return l_neighborhood.strip()

class Se3_Toc(Se3ResponseBuilder):
    def __init__(self, p_app, p_requestHandler, p_context):
        super().__init__(p_app, p_requestHandler, p_context)
        self.m_logger.info('+++ Se3_Toc created')

    def buildResponse(self):
        self.m_logger.info('Getting TOC response')
        self.m_logger.debug('p_previousContext: {0}'.format(self.m_previousContext))
        self.m_logger.debug('p_context: {0}'.format(self.m_context))

        l_dbConnection = self.m_app.getConnectionPool().getConnection()
        l_dbConnection.debugData = 'Se3_Toc.buildResponse main working connection'

        l_response = ''

        # Ta1 : Quran, surah number order
        # Ta2 : Quran, revelation order
        # Tb  : NT
        # Tc  : OT
        # T   : all scripture

        # For Quran, chapter ordering based on ST_ORDER (Surah number) or ST_ORDER_ALT (Revelation order)
        if self.m_context['K'] == 'Ta1':
            # Query for Quran only: long chapter names + Translit. No need for the Book ID
            l_query = """
                select
                    N_CHAPTER
                    , ST_NAME_OR
                    , ST_NAME_OR2
                    , ST_NAME_EN
                    , ST_NAME_FR
                from TB_CHAPTER
                where ID_BOOK = 'Qur'
                order by ST_ORDER
                ;"""
        elif self.m_context['K'] == 'Ta2':
            l_query = """
                select
                    N_CHAPTER
                    , ST_NAME_OR
                    , ST_NAME_OR2
                    , ST_NAME_EN
                    , ST_NAME_FR
                from TB_CHAPTER
                where ID_BOOK = 'Qur'
                order by ST_ORDER_ALT
                ;"""
        else:
            if self.m_context['K'] == 'Tb':
                l_cond = 'ID_GROUP_0 = "NT"'
                # title for NT
                l_response += '<h1 class="TocTitle">{0}</h1>\n'.format(
                    self.m_app.get_user_string(self.m_context, 'm_tocNTTitle')
                )
            elif self.m_context['K'] == 'Tc':
                l_cond = 'ID_GROUP_0 = "OT"'
                # title for OT
                l_response += '<h1 class="TocTitle">{0}</h1>\n'.format(
                    self.m_app.get_user_string(self.m_context, 'm_tocOTTitle')
                )
            else:
                l_cond = 'true'
                # title for All scripture
                l_response += '<h1 class="TocTitle">{0}</h1>\n'.format(
                    self.m_app.get_user_string(self.m_context, 'm_tocAllTitle')
                )

            # Query for All scripture or Bible: only chapter names + Book ID
            l_query = """
                select
                    ID_BOOK
                    , N_CHAPTER_COUNT
                    , ST_NAME_EN
                    , ST_NAME_FR
                from TB_BOOK
                where {0}
                order by ID_GROUP_0, N_ORDER
                ;""".format(l_cond)

        self.m_logger.debug('l_query: {0}'.format(l_query))
        try:
            l_cursor = l_dbConnection.cursor(buffered=True)
            l_cursor.execute(l_query)

            # Quran only (2 columns with Surah names)
            if self.m_context['K'][0:2] == 'Ta':
                # title for Quran (depending on Surah order)
                l_response += \
                    ('<h1 class="TocTitle">{0}</h1><div class="QuranToc">' + '<div class="QuranTocCol1">\n')\
                    .format(
                        self.m_app.get_user_string(self.m_context, 'm_tocQuranTitle')
                        if self.m_context['K'] == 'Ta1' else
                        self.m_app.get_user_string(self.m_context, 'm_tocQuranTitleRev')
                    )

                l_chapterCount = 1
                for l_chapter, l_nameOr, l_nameOr2, l_nameEn, l_nameFr in l_cursor:

                    l_tocLink = self.makeLinkCommon(
                        'Qur', l_chapter, '1', l_chapter,
                        p_command='P',
                        p_class='TocLink',
                        p_v2='x')

                    l_response += ('<p class="QuranSurah">' + l_tocLink +
                                   ': {0} - {1}</p>\n').format(
                        l_nameFr if self.m_context['z'] == 'fr' else l_nameEn,
                        l_nameOr2
                    )

                    # column break 1-57 / 58-114
                    if l_chapterCount == 57:
                        l_response += '</div><div class="QuranTocCol2">\n'

                    l_chapterCount += 1

                l_response += '</div></div>\n'
            # Bible & All scripture (Book name + list of chapter numbers)
            else:
                for l_bookId, l_chapterCount, l_nameEn, l_nameFr in l_cursor:
                    l_chapLinks = ' '.join([
                                               self.makeLinkCommon(
                                                   l_bookId, i, '1', i,
                                                   p_command='P',
                                                   p_class='TocLink',
                                                   p_v2='x')
                                               for i in range(1, l_chapterCount + 1)
                                               ])

                    l_response += '<p class="TocBook">{0}: {1}</p>\n'.format(
                        l_nameFr if self.m_context['z'] == 'fr' else l_nameEn, l_chapLinks
                    )

            l_cursor.close()

        except Exception as l_exception:
            self.m_logger.warning('Something went wrong {0}'.format(l_exception.args))

        self.m_app.getConnectionPool().releaseConnection(l_dbConnection)
        return l_response, self.m_context, EcAppParam.gcm_appTitle
