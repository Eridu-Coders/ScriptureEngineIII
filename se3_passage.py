# -*- coding: utf-8 -*-

from se3_utilities import *
import ec_utilities

__author__ = 'fi11222'

# -------------------------- Logger ------------------------------------------------------------------------------------
g_loggerPassage = logging.getLogger(g_appName + '.passage')
if g_verboseModeOn:
    g_loggerPassage.setLevel(logging.INFO)
if g_debugModeOn:
    g_loggerPassage.setLevel(logging.DEBUG)


# -------------------------- Passage Response --------------------------------------------------------------------------
def get_passage(p_previousContext, p_context, p_dbConnectionPool):
    g_loggerPassage.info('Getting single verse response')
    g_loggerPassage.debug('p_previousContext: {0}'.format(p_previousContext))
    g_loggerPassage.debug('p_context: {0}'.format(p_context))

    # ---------------------- Parameter check ---------------------------------------------------------------------------
    l_response = passage_control(p_context)

    if len(l_response) > 0:
        return l_response, p_context

    l_uiLanguage = p_context['z']
    l_pcBookId = g_bookAlias[p_context['b'].lower().strip()]
    l_pcChapter = p_context['c']
    l_wholeChapter = (p_context['w'] == 'x')

    # verse start/end
    if l_wholeChapter:
        # whole chapter
        l_pcVerseStart = 1
        l_pcVerseEnd = g_bookChapter[l_pcBookId][int(l_pcChapter)]
    else:
        l_pcVerseStart = p_context['v']
        l_pcVerseEnd = p_context['w']

    l_dbConnection = p_dbConnectionPool.getConnection()

    # get all attributes of the book the verse belongs to
    l_bibleQuran, l_idGroup0, l_idGroup1, l_bookPrev, l_bookNext, l_chapterShortEn, l_chapterShortFr = \
        g_bookChapter[l_pcBookId][0]

    # window title
    if l_wholeChapter:
        l_title = '{0} {1} {2}'.format(
            l_chapterShortFr if l_uiLanguage == 'fr' else l_chapterShortEn,
            l_pcChapter,
            g_appTitle)
    else:
        l_title = '{0} {1}:{2}-{3} {4}'.format(
            l_chapterShortFr if l_uiLanguage == 'fr' else l_chapterShortEn,
            l_pcChapter,
            l_pcVerseStart,
            l_pcVerseEnd,
            g_appTitle)

    # get chapter info
    l_chapterEn, l_chapterFr = get_chapter_names(p_context, l_dbConnection)

    l_groundStyle = 'pGroundHebrew'
    if l_idGroup0 == 'NT':
        l_groundStyle = 'pGroundGreek'
    elif l_idGroup0 == 'FT':
        l_groundStyle = 'pGroundArabic'

    # ---------------------- Top Banner --------------------------------------------------------------------------------
    l_topBannerTemplateString = """
        <div class="svTopBottom">
            <div class="svPrevLink">§{LeftComponent}</div>
            <div class="svNextLink">§{RightComponent}</div>
            <div class="svCenterLinks">§{CenterComponent}</div>
        </div>
    """

    l_topBannerTemplate = ec_utilities.EcTemplate(l_topBannerTemplateString)

    # link for toggling between ground text display or not
    if p_context['g']:
        l_groundToggle = '<a href="" class="UnsetParameterLink TopLink" param="{1}">{0}</a>'.format(
            get_user_string(p_context, 'p_hideGround'), g_pDisplayGround)
    else:
        l_groundToggle = '<a href="" class="SetParameterLink TopLink" param="{1}">{0}</a>'.format(
            get_user_string(p_context, 'p_displayGround'), g_pDisplayGround)

    # link for toggling between parallel or ordinary display
    if p_context['r']:
        l_parallelToggle = '<a href="" class="UnsetParameterLink TopLink" param="{1}">{0}</a>'.format(
            get_user_string(p_context, 'p_stackedVersions'), g_pParallel)
    else:
        l_parallelToggle = '<a href="" class="SetParameterLink TopLink" param="{1}">{0}</a>'.format(
            get_user_string(p_context, 'p_parallelVersions'), g_pParallel)

    # whole chapter
    if not l_wholeChapter:
        l_whole = ('<a href="" class="svGoPassage TopLink" newBook="{0}" newChapter="{1}" newVerse1="1" ' +
                   'newVerse2="x">{2}</a>').format(
                        l_pcBookId, l_pcChapter,
                        get_user_string(p_context, 'sv_wholeChapter') if l_idGroup0 != 'FT'
                        else get_user_string(p_context, 'sv_wholeSurah'))
    else:
        l_whole = ''

    if l_wholeChapter:
        # previous
        if l_pcChapter == '1':
            # previous book id since both verse and chapter are = 1
            l_previousBook = l_bookPrev
            # last chapter of the previous book
            # g_bookChapter contains for each chapter a tuple at index 0 plus a verse count value for each chapter
            # hence, the last chapter = the number of chapters = the element count of the list for this book minus one
            l_previousChapter = len(g_bookChapter[l_previousBook]) - 1
        else:
            # same book
            l_previousBook = l_pcBookId
            # decrease chapter number since > 1
            l_previousChapter = int(l_pcChapter) - 1

        # next
        if l_pcChapter == str(len(g_bookChapter[l_pcBookId]) - 1):
            # last chapter = chapter count of the book = the element count of the list for this book minus one
            # --> first chapter of next book
            l_nextBook = l_bookNext
            l_nextChapter = 1
        else:
            l_nextBook = l_pcBookId
            # can just increase chapter count since not the last one of this book
            l_nextChapter = int(l_pcChapter) + 1

        # previous and next links
        # both contain 2 attribute for the new book/chapter value + one for the tooltip (title="")
        l_previousLink = ('<a href="" class="svGoPassage TopLink" newBook="{0}" newChapter="{1}" ' +
                          'newVerse1="1" newVerse2="x" ' +
                          'title="{2}">◄</a>').format(l_previousBook, l_previousChapter,
                                                      get_user_string(p_context, 'p_PreviousLink'))

        l_nextLink = ('<a href="" class="svGoPassage TopLink" newBook="{0}" newChapter="{1}" ' +
                      'newVerse1="1" newVerse2="x" ' +
                      'title="{2}">►</a>').format(l_nextBook, l_nextChapter,
                                                  get_user_string(p_context, 'p_NextLink'))
    else:
        l_previousLink = ''
        l_nextLink = ''

    # Final top banner assembly
    l_links = l_groundToggle + l_parallelToggle + l_whole

    l_topBanner = l_topBannerTemplate.safe_substitute(
        LeftComponent=l_previousLink,
        RightComponent=l_nextLink,
        CenterComponent=l_links
    )

    # ---------------------- Verses Display ----------------------------------------------------------------------------
    # version List
    l_versions = get_version_list(p_context)

    if p_context['r']:
        # +++++++++++++++++++++ Parallel Display +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        l_response += '<table id="ParallelTable">\n'
        l_response += '<tr><td></td>\n'

        # column titles
        for l_versionId, l_versionLanguage, l_default, l_labelShort, l_labelTiny in l_versions:
            l_chapterName = l_chapterFr if l_versionLanguage == 'fr' else l_chapterEn
            if not l_wholeChapter:
                # not whole chapter
                l_chapterName += ', ' + g_userStrings[l_versionLanguage + '-' + 'p_VerseWord'] \
                    + 's ' + l_pcVerseStart \
                    + ' ' + g_userStrings[l_versionLanguage + '-' + 'p_VerseTo'] \
                    + ' ' + l_pcVerseEnd

            # Display Chapter name (+ verses if applicable)
            l_response += '<td><p class="pChapterNameParallel">{0}</h1>\n'.format(l_chapterName)

            # Display Version Name
            l_response += '<p class="pVersionNameParallel">{0}</h1></td>\n'.format(l_labelShort)

        if p_context['g']:
            # column title for ground text if displayed
            l_chapterName = (l_chapterFr if l_uiLanguage == 'fr' else l_chapterEn)
            if not l_wholeChapter:
                # not whole chapter
                l_chapterName += ', ' + get_user_string(p_context, 'p_VerseWord') \
                    + 's ' + l_pcVerseStart \
                    + ' ' + get_user_string(p_context, 'p_VerseTo') \
                    + ' ' + l_pcVerseEnd

            # Display Chapter name (+ verses if applicable)
            l_response += '<td><p class="pChapterNameParallel">{0}</h1>\n'.format(l_chapterName)

            # Display Version Name
            l_response += '<p class="pVersionNameParallel">{0}</h1></td>\n'.format(
                get_user_string(p_context, 'p_GroundText'))

        # end of title row
        l_response += '</tr>\n'

        # Verse List -----------------------------------------------------------------------------------------------
        l_versionVector = get_version_vector(p_context)
        if p_context['g']:
            l_versionVector += ', "_gr"'

        l_query = """
            select
                N.ID_VERSION
                , N.ID_BOOK
                , N.N_CHAPTER
                , N.N_VERSE
                , V.TX_VERSE_INSENSITIVE
            from
                TB_VERSES_SQUARED N left outer join TB_VERSES V on
                    V.ID_VERSION = N.ID_VERSION
                    and V.ID_BOOK = N.ID_BOOK
                    and V.N_CHAPTER = N.N_CHAPTER
                    and V.N_VERSE = N.N_VERSE
            where
                N.ID_VERSION in ({4})
                and N.ID_BOOK = '{0}'
                and N.N_CHAPTER = {1}
                and N.N_VERSE >= {2}
                and N.N_VERSE <= {3}
            order by N.N_VERSE, N.N_ORDER
            ;""".format(l_pcBookId, l_pcChapter, l_pcVerseStart, l_pcVerseEnd, l_versionVector)

        g_loggerPassage.debug('l_query {0}'.format(l_query))
        try:
            l_cursor = l_dbConnection.cursor(buffered=True)
            l_cursor.execute(l_query)

            # the version ID of the leftmost column
            l_versionLeft = l_versions[0][0]
            l_start = True
            for l_versionId, l_bookId, l_chapterNumber, l_verseNumber, l_verseText in l_cursor:
                if l_versionId == l_versionLeft:
                    if l_start:
                        l_start = False
                    else:
                        l_response += '</tr>'

                    l_response += ('<tr><td class="pVerseRef">' +
                                   '<a href="" class="GoOneVerse" pBook="{0}" pChapter="{1}" pVerse="{2}">' +
                                   '{3} {1}:{2}</a></td>').format(
                                   l_bookId, l_chapterNumber, l_verseNumber,
                                   l_chapterShortFr if l_uiLanguage == 'fr' else l_chapterShortEn,
                                   l_verseText)

                if l_verseText is None:
                    l_verseText = '<span class="pMessage">{0}</span>'.format(
                        get_user_string(p_context, 'p_noText'))

                if l_versionId == '_gr':
                    l_verseText = '<span class="{0}">{1}</span>'.format(l_groundStyle, l_verseText)
                    l_response += '<td class="{0}">{1}</td>'.format(
                        'LRText' if l_idGroup0 == 'NT' else 'RLText', l_verseText)
                else:
                    l_response += '<td><span class="TranslationText">{0}</span></td>'.format(l_verseText)

            l_response += '</tr>'
            l_cursor.close()
        except Exception as l_exception:
            g_loggerPassage.warning('Something went wrong {0}'.format(l_exception.args))

        # end of parallel table
        l_response += '</table>\n'
    else:
        # +++++++++++++++++++++ Stacked Display ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        for l_versionId, l_versionLanguage, l_default, l_labelShort, l_labelTiny in l_versions:
            l_chapterName = l_chapterFr if l_versionLanguage == 'fr' else l_chapterEn
            if not l_wholeChapter:
                # not whole chapter
                l_chapterName += ', ' + g_userStrings[l_versionLanguage + '-' + 'p_VerseWord'] \
                    + 's ' + l_pcVerseStart \
                    + ' ' + g_userStrings[l_versionLanguage + '-' + 'p_VerseTo'] \
                    + ' ' + l_pcVerseEnd

            # Display Chapter name (+ verses if applicable)
            l_response += '<h1 class="pChapterName">{0}</h1>\n'.format(l_chapterName)

            # Display Version Name
            l_response += '<h2 class="pVersionName">{0}</h1>\n'.format(l_labelShort)

            # Verse List -----------------------------------------------------------------------------------------------
            l_query = """
                select
                    TX_VERSE_INSENSITIVE
                    , N_VERSE
                from TB_VERSES
                where
                    ID_VERSION = '{4}'
                    and ID_BOOK = '{0}'
                    and N_CHAPTER = {1}
                    and N_VERSE >= {2}
                    and N_VERSE <= {3}
                order by N_VERSE
                ;""".format(l_pcBookId, l_pcChapter, l_pcVerseStart, l_pcVerseEnd, l_versionId)

            g_loggerPassage.debug('l_query {0}'.format(l_query))
            try:
                l_cursor = l_dbConnection.cursor(buffered=True)
                l_cursor.execute(l_query)

                for l_verseText, l_verseNumber in l_cursor:
                    l_response += makeVerse(l_pcBookId, l_pcChapter, l_verseNumber, l_verseText,
                                            l_chapterShortFr if l_versionLanguage == 'fr' else l_chapterShortEn)

                l_cursor.close()
            except Exception as l_exception:
                g_loggerPassage.warning('Something went wrong {0}'.format(l_exception.args))

        # Ground Text --------------------------------------------------------------------------------------------------
        if p_context['g']:
            l_chapterName = (l_chapterFr if l_uiLanguage == 'fr' else l_chapterEn)
            if not l_wholeChapter:
                # not whole chapter
                l_chapterName += ', ' + get_user_string(p_context, 'p_VerseWord') \
                    + 's ' + l_pcVerseStart \
                    + ' ' + get_user_string(p_context, 'p_VerseTo') \
                    + ' ' + l_pcVerseEnd

            # Display Chapter name (+ verses if applicable)
            l_response += '<h1 class="pChapterName">{0}</h1>\n'.format(l_chapterName)

            # Display Version Name
            l_response += '<h2 class="pVersionName">{0}</h1>\n'.format(get_user_string(p_context, 'p_GroundText'))

            l_query = """
                select
                    TX_VERSE_INSENSITIVE
                    , N_VERSE
                from TB_VERSES
                where
                    ID_BOOK = '{0}'
                    and N_CHAPTER = {1}
                    and N_VERSE >= {2}
                    and N_VERSE <= {3}
                    and ID_VERSION = '_gr'
                order by N_VERSE
                ;""".format(l_pcBookId, l_pcChapter, l_pcVerseStart, l_pcVerseEnd)

            g_loggerPassage.debug('l_query {0}'.format(l_query))
            try:
                l_cursor = l_dbConnection.cursor(buffered=True)
                l_cursor.execute(l_query)

                for l_verseText, l_verseNumber in l_cursor:
                    # l_verseText = '<span class="{0}">{1}</span>'.format(l_groundStyle, l_verseText)
                    if l_idGroup0 == 'NT':
                        # left to right for Greek
                        l_response += makeVerse(l_pcBookId, l_pcChapter, l_verseNumber, l_verseText,
                                                l_chapterShortFr if l_uiLanguage == 'fr' else l_chapterShortEn)
                    else:
                        # right to left otherwise
                        l_response += makeVerse(l_pcBookId, l_pcChapter, l_verseNumber, l_verseText,
                                                l_chapterShortFr if l_uiLanguage == 'fr' else l_chapterShortEn, True)

                l_cursor.close()
            except Exception as l_exception:
                g_loggerPassage.warning('Something went wrong {0}'.format(l_exception.args))

    # ----------------- Final Page Assembly ----------------------------------------------------------------------------

    # top banner both at top and at bottom of single verse table
    l_response = l_topBanner + l_response + l_topBanner

    p_dbConnectionPool.releaseConnection(l_dbConnection)

    return l_response, p_context, l_title
