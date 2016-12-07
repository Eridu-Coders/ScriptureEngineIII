# -*- coding: utf-8 -*-

import json

from se3_utilities import *
from ec_app_core import *
from se3_app_param import *

__author__ = 'fi11222'

class Se3_SingleVerse(Se3ResponseBuilder):
    def __init__(self, p_app, p_requestHandler, p_context):
        super().__init__(p_app, p_requestHandler, p_context)
        self.m_logger.info('+++ Se3_SingleVerse created')

    # ---------------------- Single verse HTML response ----------------------------------------------------------------
    def buildResponse(self):
        self.m_logger.info('Getting single verse response')
        self.m_logger.debug('p_previousContext: {0}'.format(self.m_previousContext))
        self.m_logger.debug('p_context: {0}'.format(self.m_context))
    
        # ---------------------- Parameter check ---------------------------------------------------------------------------
        l_response = self.m_app.verse_control(self.m_context)
    
        if len(l_response) > 0:
            return l_response, self.m_context, 'Error'
    
        l_uiLanguage = self.m_context['z']
        l_pcBookId = self.m_app.getBookFromAlias(self.m_context['b'].lower().strip())
        l_pcChapter = self.m_context['c']
        l_pcVerse = self.m_context['v']
    
        self.m_logger.debug('l_pcBookId: {0}'.format(l_pcBookId))
        self.m_logger.debug('self.m_context[K]: {0}'.format(self.m_context['K']))
    
        l_dbConnection = self.m_app.getConnectionPool().getConnection()
        l_dbConnection.debugData = 'Se3_SingleVerse.buildResponse main working connection'

        # get all attributes of the book the verse belongs to
        l_bibleQuran, l_idGroup0, l_idGroup1, l_bookPrev, l_bookNext, l_nameEn, l_nameFr = \
            self.m_app.getBookAttributes(l_pcBookId)
            #self.m_app.m_bookChapter[l_pcBookId][0]
    
        l_verseRef = '{0} {1}:{2}'.format(
            l_nameFr if l_uiLanguage == 'fr' else l_nameEn,
            l_pcChapter,
            l_pcVerse)
    
        # window title
        l_title = l_verseRef + '-' + EcAppParam.gcm_appTitle
    
        # start of response string
        l_response = '<table id="svOuterTable">\n'
    
        # ----------------- Top Banner -------------------------------------------------------------------------------------
        l_topBanner = self.topBanner(l_idGroup0, l_pcVerse, l_pcChapter, l_bookPrev, l_pcBookId, l_bookNext)
    
        # ----------------- Verse Title ------------------------------------------------------------------------------------
        l_chapterEn, l_chapterFr = self.m_app.get_chapter_names(self.m_context, l_dbConnection)
    
        l_chapterName = (l_chapterFr if l_uiLanguage == 'fr' else l_chapterEn) \
            + ', ' + EcAppCore.get_user_string(self.m_context, 'p_VerseWord') \
            + ' ' + l_pcVerse
    
        l_response += '<tr><td colspan="2" class="svVerseTitle">{0}</td></tr>\n'.format(l_chapterName)
    
        # ----------------- Ground Text ------------------------------------------------------------------------------------
        # HTML style used here and for the interlinear displays
        l_groundStyle = 'svGroundHebrew'
        if l_idGroup0 == 'NT':
            l_groundStyle = 'svGroundGreek'
        elif l_idGroup0 == 'FT':
            l_groundStyle = 'svGroundArabic'
    
        l_query = """
            select TX_VERSE_INSENSITIVE
            from TB_VERSES
            where
                ID_BOOK = '{0}'
                and N_CHAPTER = {1}
                and N_VERSE = {2}
                and ID_VERSION = '_gr'
            ;""".format(l_pcBookId, l_pcChapter, l_pcVerse)
    
        self.m_logger.debug('l_query {0}'.format(l_query))
        try:
            l_cursor = l_dbConnection.cursor(buffered=True)
            l_cursor.execute(l_query)
    
            for l_ground, in l_cursor:
                l_response += '<tr><td colspan="2" class="{0}">{1}</td></tr>\n'.format(l_groundStyle, l_ground)
    
            l_cursor.close()
        except Exception as l_exception:
            self.m_logger.warning('Something went wrong {0}'.format(l_exception.args))
    
        # ------------------------------------------------------------------------------------------------------------------
        # All interlinear HTML segments below are strings of svInterlinearWord tables
        # the style makes them inline blocks
    
        l_lxxDisplayed = l_idGroup0 == 'OT' and self.m_context['x']
        l_kjvOrNasbDisplayed = (l_idGroup0 == 'OT' or l_idGroup0 == 'NT') and (self.m_context['k'] or self.m_context['n'])
    
        # number of rows that the verse reference will span vertically
        l_refRowSpan = 1
        if l_lxxDisplayed:
            l_refRowSpan += 1
        if l_kjvOrNasbDisplayed:
            l_refRowSpan += 1
    
        # ----------------- Verse Ref --------------------------------------------------------------------------------------
        l_response += '<tr><td rowspan="{0}" class="vVerseRef">{1}</td>\n'.format(l_refRowSpan, l_verseRef)
    
        # ----------------- Interlinear ------------------------------------------------------------------------------------
        # Quran Corpus interlinear for the Quran and Bible Hub for the rest
        if l_idGroup0 == 'FT':
            l_interlinearId = 'C'
        else:
            l_interlinearId = 'H'
    
        l_query = """
            select
                ST_GROUND
                , ST_PUNCT
                , ST_TRANSLIT
                , TX_TRANSLATION
                , TX_GRAMMAR
                , N_WORD
                , ID_STRONGS
            from TB_INTERLINEAR
            where
                ID_BOOK = '{0}'
                and N_CHAPTER = {1}
                and N_VERSE = {2}
                and ID_INTERL = '{3}'
            order by N_WORD
            ;""".format(l_pcBookId, l_pcChapter, l_pcVerse, l_interlinearId)
    
        self.m_logger.debug('l_query {0}'.format(l_query))
        try:
            l_cursor = l_dbConnection.cursor(buffered=True)
            l_cursor.execute(l_query)
    
            l_interlinearHtml = ''
            for l_ground, l_punct, l_translit, l_translation, l_grammar, l_word, l_idStrongs in l_cursor:
    
                # word link
                if len(l_ground.strip()) == 0:
                    l_links = '&nbsp;'
                else:
                    l_links = self.makeLinkCommon(
                        l_pcBookId, l_pcChapter, l_pcVerse, l_ground,
                        p_command='W',
                        p_class='WordLink',
                        p_wordId=str(l_word) + '-' + l_interlinearId + '-' + l_idStrongs)
    
                # values are replaced with &nbsp; if empty in order to avoid collapsed cells
                l_translit = '&nbsp;' if len(l_translit.strip()) == 0 else l_translit.strip()
                l_translation = '&nbsp;' if len(l_translation.strip()) == 0 else l_translation.strip()
                l_grammar = '&nbsp;' if len(l_grammar.strip()) == 0 else l_grammar.strip()
    
                # punctuation is displayed in a cell by itself spanning all 4 lines if non empty
                # grammar is not displayed for the Quran (too long)
                l_interlinearHtml += '<table class="svInterlinearWord">\n' + \
                    '<tr>' + \
                    '<td class="{1}">{0}</td>'.format(l_links, l_groundStyle) + \
                    ('<td class="svPunct" rowspan="4">{0}</td>'.format(l_punct) if len(l_punct) > 0 else '') + \
                    '</tr>\n' + \
                    '<tr><td class="svTranslit">{0}</td></tr>\n'.format(l_translit) + \
                    '<tr><td><span class="TranslationText">{0}</span></td></tr>\n'.format(l_translation) + \
                    ('<tr><td class="svGrammar">{0}</td></tr>\n'.format(l_grammar) if l_idGroup0 != 'FT' else '') + \
                    '</table>\n'
    
            # the svInterlinearBox style is just a normal svOuterTable td with its own sets of padding, etc.
            l_response += '<td class="svInterlinearBox">{0}</td></tr>\n'.format(l_interlinearHtml)
    
            l_cursor.close()
        except Exception as l_exception:
            self.m_logger.warning('Something went wrong {0}'.format(l_exception.args))
    
        self.m_logger.debug('self.m_context[K] H: {0}'.format(self.m_context['K']))
    
        # ----------------- LXX --------------------------------------------------------------------------------------------
        # only available for OT obviously
        if l_lxxDisplayed:
            l_query = """
                select
                    ST_GROUND
                    , TX_STRONGS_LIST
                    , TX_TRANSLATION
                    , N_WORD
                from TB_INTERLINEAR
                where
                    ID_BOOK = '{0}'
                    and N_CHAPTER = {1}
                    and N_VERSE = {2}
                    and ID_INTERL = 'L'
                order by N_WORD
                ;""".format(l_pcBookId, l_pcChapter, l_pcVerse)
    
            self.m_logger.debug('l_query {0}'.format(l_query))
            try:
                l_cursor = l_dbConnection.cursor(buffered=True)
                l_cursor.execute(l_query)
    
                l_interlinearHtml = ''
                for l_ground, l_strongsVector, l_translation, l_word in l_cursor:
                    if len(l_ground.strip()) == 0:
                        # no ground text at all --> &nbsp; to avoid collapsed cell
                        l_links = '&nbsp;'
                    else:
                        # list of words in the ground text
                        l_wordList = l_ground.split(' ')
                        # corresponding list of Strong's IDs
                        l_strongsList = json.loads(l_strongsVector)
    
                        # Warning if 2 lists do not have same length
                        if len(l_strongsList) != len(l_wordList):
                            self.m_logger.warning(
                                ('{0} {1}:{2}.{3} - Length of ground text [{4}] and ' +
                                 'Strong\'s ID list [{5}] do not match').format(
                                    l_pcBookId, l_pcChapter, l_pcVerse, l_word, l_ground, l_strongsVector
                                )
                            )
    
                        # make list of links for those words that have a strong's ID (those with 'NoStrong'
                        # are just the ground text word without link)
                        l_links = ' '.join(
                            [
                                (
                                    l_groundWord if l_strongsId == 'NoStrong' else
                                    self.makeLinkCommon(
                                        l_pcBookId, l_pcChapter, l_pcVerse, l_groundWord,
                                        p_command='W',
                                        p_class='WordLink',
                                        p_wordId=str(l_word) + '-' + 'L' + '-' + l_strongsId)
                                )
                                for l_strongsId, l_groundWord in zip(l_strongsList, l_wordList)
                            ]
                        )
    
                    # l_links = '&nbsp;' if len(l_links.strip()) == 0 else l_links.strip()
                    l_translation = '&nbsp;' if len(l_translation.strip()) == 0 else l_translation.strip()
    
                    # remove lint from the LXX translation text
                    # TODO clean that up in the DB
                    l_translation = re.sub('<[^>]+>', '', l_translation)
                    l_translation = re.sub('[0-9]', '', l_translation)
                    l_translation = re.sub('[][]', '', l_translation)
                    l_translation = re.sub('\s+', ' ', l_translation).strip()
    
                    l_interlinearHtml += '<table class="svInterlinearWord">\n' + \
                        '<tr><td class="svGroundGreek">{0}</td></tr>\n'.format(l_links) + \
                        '<tr><td><span class="TranslationText">{0}</span></td></tr>\n'.format(l_translation) + \
                        '</table>\n'
    
                # link to hide LXX
                # on click --> jQuery function un-sets this bit mask (g_svDisplayLxx)
                l_hideLxx = '<a href="" class="UnsetParameterLink" param="{1}">{0}</a>'.format(
                    EcAppCore.get_user_string(self.m_context, 'sv_HideLxx'), Se3AppParam.gcm_svDisplayLxx)
    
                # add this link in another inline block table floating to the right (as specified in the CSS)
                l_interlinearHtml += '<table class="svInterlinearWord svInterlinearWordLink">\n' + \
                    '<tr><td>&nbsp;</td></tr>\n<tr><td>&nbsp;{0}</td></tr>\n'.format(l_hideLxx) + \
                    '</table>\n'
    
                # the svInterlinearBox style is just a normal svOuterTable td with its own sets of padding, etc.
                l_response += '<tr><td class="svInterlinearBox">{0}</td></tr>\n'.format(l_interlinearHtml)
    
                l_cursor.close()
            except Exception as l_exception:
                self.m_logger.warning('Something went wrong {0}'.format(l_exception.args))
    
        # ----------------- KJV & NASB -------------------------------------------------------------------------------------
        # both are display in the same sequence of svInterlinearWord tables each one in its own translation cell
        # as ground text and transliteration are the same
    
        # this whole segment appears only for the Bible (obviously) and whether one or the other (or both) the
        # KJV or NASB is selected
        if l_kjvOrNasbDisplayed:
            l_query = """
                select
                    ST_GROUND
                    , ST_TRANSLIT
                    , TX_TRANSLATION
                    , ST_TRANS_ALT
                    , N_WORD
                    , ID_STRONGS
                from TB_INTERLINEAR
                where
                    ID_BOOK = '{0}'
                    and N_CHAPTER = {1}
                    and N_VERSE = {2}
                    and ID_INTERL = 'K'
                order by N_WORD
                ;""".format(l_pcBookId, l_pcChapter, l_pcVerse)
    
            self.m_logger.debug('l_query {0}'.format(l_query))
            try:
                l_cursor = l_dbConnection.cursor(buffered=True)
                l_cursor.execute(l_query)
    
                l_interlinearHtml = ''
                for l_ground, l_translit, l_translKjv, l_translNasb, l_word, l_idStrongs in l_cursor:
    
                    # word link
                    if len(l_ground.strip()) == 0:
                        l_links = '&nbsp;'
                    else:
                        l_links = self.makeLinkCommon(
                            l_pcBookId, l_pcChapter, l_pcVerse, l_ground,
                            p_command='W',
                            p_class='WordLink',
                            p_wordId=str(l_word) + '-' + 'K' + '-' + l_idStrongs)
    
                    # values are replaced with &nbsp; if empty in order to avoid collapsed cells
                    l_links = '&nbsp;' if len(l_links.strip()) == 0 else l_links.strip()
                    l_translKjv = '&nbsp;' if len(l_translKjv.strip()) == 0 else l_translKjv.strip()
                    l_translNasb = '&nbsp;' if len(l_translNasb.strip()) == 0 else l_translNasb.strip()
    
                    # KJV and NASB translations are displayed only if the appropriate context flag is set
                    l_interlinearHtml += '<table class="svInterlinearWord">\n' + \
                        '<tr><td class="{1}">{0}</td></tr>\n'.format(l_links, l_groundStyle) + \
                        '<tr><td class="svTranslit">{0}</td></tr>\n'.format(l_translit) + \
                        ('<tr><td><span class="TranslationText">{0}</span></td></tr>\n'.format(l_translKjv)
                         if self.m_context['k'] else '') + \
                        ('<tr><td><span class="TranslationText">{0}</span></td></tr>\n'.format(l_translNasb)
                         if self.m_context['n'] else '') + \
                        '</table>\n'
    
                # link to hide KJV/NASB
                # on click --> jQuery function un-sets this bit mask (g_svDisplayKjv or g_svDisplayNasb)
                l_hideKjv = '<a href="" class="UnsetParameterLink" param="{1}">{0}</a>'.format(
                    EcAppCore.get_user_string(self.m_context, 'sv_HideKjv'), Se3AppParam.gcm_svDisplayKjv)
                l_hideNasb = '<a href="" class="UnsetParameterLink" param="{1}">{0}</a>'.format(
                    EcAppCore.get_user_string(self.m_context, 'sv_HideNasb'), Se3AppParam.gcm_svDisplayNasb)
    
                # add this link in another inline block table floating to the right (as specified in the CSS)
                l_interlinearHtml += '<table class="svInterlinearWord svInterlinearWordLink">\n' + \
                    '<tr><td>&nbsp;</td></tr><tr><td>&nbsp;</td></tr>\n' + \
                    ('<tr><td>&nbsp;{0}</td></tr>\n'.format(l_hideKjv) if self.m_context['k'] else '') + \
                    ('<tr><td>&nbsp;{0}</td></tr>\n'.format(l_hideNasb) if self.m_context['n'] else '') + \
                    '</table>\n'
    
                # the svInterlinearBox style is just a normal svOuterTable td with its own sets of padding, etc.
                l_response += '<tr><td class="svInterlinearBox">{0}</td></tr>\n'.format(l_interlinearHtml)
    
                l_cursor.close()
            except Exception as l_exception:
                self.m_logger.warning('Something went wrong {0}'.format(l_exception.args))
    
        self.m_logger.info('self.m_context[K] K: {0}'.format(self.m_context['K']))
    
        # ----------------- List of translations -----------------------------------------------------------------------
        l_response += self.translationList(l_pcBookId, l_pcChapter, l_pcVerse, l_dbConnection)
    
        # ----------------- End of table -------------------------------------------------------------------------------
        l_response += '</table>\n'
    
        # top banner both at top and at bottom of single verse table
        l_response = l_topBanner + l_response + l_topBanner
    
        self.m_app.getConnectionPool().releaseConnection(l_dbConnection)
        self.m_logger.debug('self.m_context[K] End: {0}'.format(self.m_context['K']))
    
        return l_response, self.m_context, l_title

    def translationList(self, p_pcBookId, p_pcChapter, p_pcVerse, p_dbConnection):
        # title box at the top of the translations section
        l_tl = '<tr><td colspan="2" class="svTranslationsTitle">{0}</td></tr>\n'.format(
            EcAppCore.get_user_string(self.m_context, 'sv_TranslationsTitle'))
    
        # set of version Ids. If self.m_context['a'] = 1 then all versions
        l_versionVector = self.m_app.get_version_vector(self.m_context, self.m_context['a'])
    
        l_query = """
            select
                V.TX_VERSE_INSENSITIVE
                , N.ST_LABEL_TINY
            from TB_VERSES V join TB_VERSION N on V.ID_VERSION = N.ID_VERSION
            where
                V.ID_VERSION in ({0})
                and V.ID_VERSION <> '_gr'
                and V.ID_BOOK = '{1}'
                and V.N_CHAPTER = {2}
                and V.N_VERSE = {3}
            order by N.N_ORDER
            ;""".format(l_versionVector, p_pcBookId, p_pcChapter, p_pcVerse)
    
        self.m_logger.debug('l_query {0}'.format(l_query))
        try:
            l_cursor = p_dbConnection.cursor(buffered=True)
            l_cursor.execute(l_query)
    
            for l_verseText, l_versionLabel in l_cursor:
                l_tl += ('<tr><td class="svVersionLabel">{0}</td>' +
                         '<td class="svVerseText"><span class="TranslationText">{1}</span></td></tr>\n').format(
                    l_versionLabel, l_verseText)
    
            l_cursor.close()
        except Exception as l_exception:
            self.m_logger.warning('Something went wrong {0}'.format(l_exception.args))
    
        return l_tl
    
    
    def topBanner(self, p_idGroup0, p_pcVerse, p_pcChapter, p_bookPrev, p_pcBookId, p_bookNext):
        l_topBannerTemplateString = """
            <div class="svTopBottom">
                <div class="svPrevLink">§{LeftComponent}</div>
                <div class="svNextLink">§{RightComponent}</div>
                <div class="svCenterLinks">§{CenterComponent}</div>
            </div>
        """
    
        l_topBannerTemplate = EcTemplate(l_topBannerTemplateString)
    
        # in all 4 links below, the HTML attribute param="" is a bit mask which will be set or unset by a
        # javascript jQuery function upon a click on the link
    
        # link for toggling between all versions and selected versions
        if self.m_context['a']:
            l_allToggle = '<a href="" class="UnsetParameterLink TopLink" param="{1}">{0}</a>'.format(
                EcAppCore.get_user_string(self.m_context, 'sv_SelectedVersions'), Se3AppParam.gcm_svAllVersions)
        else:
            l_allToggle = '<a href="" class="SetParameterLink TopLink" param="{1}">{0}</a>'.format(
                EcAppCore.get_user_string(self.m_context, 'sv_AllVersions'), Se3AppParam.gcm_svAllVersions)
    
        # link for displaying NASB interlinear if applicable and not already displayed
        if (p_idGroup0 == 'OT' or p_idGroup0 == 'NT') and not self.m_context['n']:
            l_displayNasb = '<a href="" class="SetParameterLink TopLink" param="{1}">{0}</a>'.format(
                EcAppCore.get_user_string(self.m_context, 'sv_DisplayNasb'), Se3AppParam.gcm_svDisplayNasb)
        else:
            l_displayNasb = ''
    
        # link for displaying KJV interlinear if applicable and not already displayed
        if (p_idGroup0 == 'OT' or p_idGroup0 == 'NT') and not self.m_context['k']:
            l_displayKjv = '<a href="" class="SetParameterLink TopLink" param="{1}">{0}</a>'.format(
                EcAppCore.get_user_string(self.m_context, 'sv_DisplayKjv'), Se3AppParam.gcm_svDisplayKjv)
        else:
            l_displayKjv = ''
    
        # link for displaying LXX interlinear if applicable and not already displayed
        if p_idGroup0 == 'OT' and not self.m_context['x']:
            l_displayLxx = '<a href="" class="SetParameterLink TopLink" param="{1}">{0}</a>'.format(
                EcAppCore.get_user_string(self.m_context, 'sv_DisplayLxx'), Se3AppParam.gcm_svDisplayLxx)
        else:
            l_displayLxx = ''
    
        # components of the previous and next links
    
        # Previous
        if p_pcVerse == '1':
            if p_pcChapter == '1':
                # previous book id since both verse and chapter are = 1
                l_previousBook = p_bookPrev
                # last chapter of the previous book
                l_previousChapter = self.m_app.chapterCount(l_previousBook)
                #l_previousChapter = len(self.m_app.m_bookChapter[l_previousBook]) - 1
            else:
                # same book
                l_previousBook = p_pcBookId
                # decrease chapter number since > 1
                l_previousChapter = int(p_pcChapter) - 1
    
            # verse number = las verse of the new chapter = verse count of this chapter (numbering starts at 1)
            l_previousVerse = self.m_app.getChapterVerseCount(l_previousBook, l_previousChapter)
            #l_previousVerse = self.m_app.m_bookChapter[l_previousBook][l_previousChapter]
        else:
            # simplest case: just need to decrease verse number
            l_previousBook = p_pcBookId
            l_previousChapter = p_pcChapter
            l_previousVerse = int(p_pcVerse) - 1
    
        # Next
        #if p_pcVerse == str(self.m_app.m_bookChapter[p_pcBookId][int(p_pcChapter)]):
        if p_pcVerse == str( self.m_app.getChapterVerseCount(p_pcBookId, int(p_pcChapter)) ):
            # last verse of the chapter = verse cont for that chapter
            #if p_pcChapter == str(len(self.m_app.m_bookChapter[p_pcBookId]) - 1):
            if p_pcChapter == str(self.m_app.chapterCount(p_pcBookId)):
                # last chapter = chapter count of the book = the element count of the list for this book minus one
                # --> first chapter of next book
                l_nextBook = p_bookNext
                l_nextChapter = 1
            else:
                l_nextBook = p_pcBookId
                # can just increase chapter count since not the last one of this book
                l_nextChapter = int(p_pcChapter) + 1
    
            # first verse of the new chapter
            l_nextVerse = 1
        else:
            # simplest case: just increase the verse number as it is not the last one of the chapter
            l_nextBook = p_pcBookId
            l_nextChapter = p_pcChapter
            l_nextVerse = int(p_pcVerse) + 1
    
        # previous and next links
        # both contain 3 attribute for the new book/chapter/verse value + one for the tooltip (title="")
        l_previousLink = self.makeLinkCommon(l_previousBook, l_previousChapter, l_previousVerse, '◄',
                                             p_toolTip=EcAppCore.get_user_string(self.m_context, 'sv_PreviousLink'))
    
        l_nextLink = self.makeLinkCommon(l_nextBook, l_nextChapter, l_nextVerse, '►',
                                         p_toolTip=EcAppCore.get_user_string(self.m_context, 'sv_NextLink'))
    
        # 5 adjacent verses
        l_5start = max(int(p_pcVerse) - 2, 1)
        l_5end = min(l_5start + 4, self.m_app.getChapterVerseCount(p_pcBookId, int(p_pcChapter)))
        #l_5end = min(l_5start + 4, self.m_app.m_bookChapter[p_pcBookId][int(p_pcChapter)])
        if l_5end - l_5start < 4:
            l_5start = max(l_5end - 4, 1)
    
        l_5Link = self.makeLinkCommon(
            p_pcBookId, p_pcChapter, l_5start,
            EcAppCore.get_user_string(self.m_context, 'sv_5Neighborhood'),
            p_command='P',
            p_class='TopLink',
            p_v2=l_5end)
    
        # 9 adjacent verses
        l_9start = max(int(p_pcVerse) - 4, 1)
        l_9end = min(l_9start + 8, self.m_app.getChapterVerseCount(p_pcBookId, int(p_pcChapter)))
        #l_9end = min(l_9start + 8, self.m_app.m_bookChapter[p_pcBookId][int(p_pcChapter)])
        if l_9end - l_9start < 8:
            l_9start = max(l_9end - 8, 1)
    
        l_9Link = self.makeLinkCommon(
            p_pcBookId, p_pcChapter, l_9start,
            EcAppCore.get_user_string(self.m_context, 'sv_9Neighborhood'),
            p_command='P',
            p_class='TopLink',
            p_v2=l_9end)
    
        # whole chapter
        l_whole = self.makeLinkCommon(
            p_pcBookId, p_pcChapter, '1',
            EcAppCore.get_user_string(self.m_context, 'sv_wholeChapter') if p_idGroup0 != 'FT'
            else EcAppCore.get_user_string(self.m_context, 'sv_wholeSurah'),
            p_command='P',
            p_class='TopLink',
            p_v2='x')
    
        # Final top banner assembly
        l_links = l_allToggle + l_displayLxx + l_displayKjv + l_displayNasb + l_5Link + l_9Link + l_whole
    
        l_topBanner = l_topBannerTemplate.safe_substitute(
            LeftComponent=l_previousLink,
            RightComponent=l_nextLink,
            CenterComponent=l_links
        )
    
        return l_topBanner
