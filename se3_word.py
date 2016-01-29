# -*- coding: utf-8 -*-

from se3_utilities import *

__author__ = 'fi11222'

# -------------------------- Logger ------------------------------------------------------------------------------------
g_loggerWord = logging.getLogger(ec_app_params.g_appName + '.word')
if ec_app_params.g_verboseModeOn:
    g_loggerWord.setLevel(logging.INFO)
if ec_app_params.g_debugModeOn:
    g_loggerWord.setLevel(logging.DEBUG)


# -------------------------- Word Response -----------------------------------------------------------------------------
def get_word(p_previousContext, p_context, p_dbConnectionPool):
    g_loggerWord.info('Getting single word response')
    g_loggerWord.debug('p_previousContext: {0}'.format(p_previousContext))
    g_loggerWord.debug('p_context: {0}'.format(p_context))

    # ---------------------- Parameter check ---------------------------------------------------------------------------
    l_response = word_control(p_context)

    if len(l_response) > 0:
        return l_response, p_context, 'Error'

    l_uiLanguage = p_context['z']
    l_pcBookId = g_bookAlias[p_context['b'].lower().strip()]
    l_pcChapter = p_context['c']
    l_pcVerse = p_context['v']

    # split components of the word field
    l_pcWordId = p_context['d'].split('-')[0]
    l_pcInterlinearId = p_context['d'].split('-')[1]
    l_pcIdStrongs = p_context['d'].split('-')[2]

    l_dbConnection = p_dbConnectionPool.getConnection()

    # get all attributes of the book the verse belongs to
    l_bibleQuran, l_idGroup0, l_idGroup1, l_bookPrev, l_bookNext, l_chapterShortEn, l_chapterShortFr = \
        g_bookChapter[l_pcBookId][0]

    # ground text style based on book collection
    l_groundStyle = 'wGroundHebrew'
    if l_idGroup0 == 'NT':
        l_groundStyle = 'wGroundGreek'
    elif l_idGroup0 == 'FT':
        l_groundStyle = 'wGroundArabic'

    # window title
    l_title = ec_app_params.g_appTitle

    # response start
    l_response = '<table id="wOuterTable">'

    # -------------------- Top Box -------------------------------------------------------------------------------------
    if l_pcWordId == '_':
        # there is no specific word number given --> get lexicon info directly through strongs number
        l_query = """
            select
                R.ST_GROUND as ST_GROUND_ROOT
                , R.ST_TRANSLIT as ST_TRANSLIT_ROOT
                , R.ID_ROOT
                , L.ST_TRANSLIT
                , L.ST_GROUND
                , L.ST_TYPE
                , L.TX_DEF_SHORT
                , L.TX_DEF
                , L.TX_DERIVATION
                , L.TX_USAGE
                , L.TX_FREQ_A
                , L.TX_FREQ_B
                , L.TX_DICT
                , L.TX_DICT_IMAGE
                , '' as ST_GROUND_WORD
                , '' as ST_TRANSLIT_WORD
                , '' as TX_TRANSLATION
                , '' as TX_GRAMMAR
                , '' as TX_GRAMMAR_LONG
                , '' as ST_WORD_IMG
            from TB_LEXICON L left outer join V_ROOT_STRONGS R on L.ID_STRONGS = R.ID_STRONGS
            where
                L.ID_STRONGS = '{0}'
            ;""".format(l_pcIdStrongs)
    else:
        # there is a word number -->
        # get word info through book/chapter/verse/word (+ interlinear id) and then lexicon info through a join
        l_query = """
            select
                R.ST_GROUND as ST_GROUND_ROOT
                , R.ST_TRANSLIT as ST_TRANSLIT_ROOT
                , R.ID_ROOT
                , L.ST_TRANSLIT
                , L.ST_GROUND
                , L.ST_TYPE
                , L.TX_DEF_SHORT
                , L.TX_DEF
                , L.TX_DERIVATION
                , L.TX_USAGE
                , L.TX_FREQ_A
                , L.TX_FREQ_B
                , L.TX_DICT
                , L.TX_DICT_IMAGE
                , I.ST_GROUND as ST_GROUND_WORD
                , I.ST_TRANSLIT as ST_TRANSLIT_WORD
                , I.TX_TRANSLATION
                , I.TX_GRAMMAR
                , I.TX_GRAMMAR_LONG
                , I.ST_WORD_IMG
            from (TB_LEXICON L join V_INTERLINEAR I on L.ID_STRONGS = I.ID_STRONGS)
                    left outer join V_ROOT_STRONGS R on L.ID_STRONGS = R.ID_STRONGS
            where
                I.ID_BOOK = '{0}'
                and I.N_CHAPTER = {1}
                and I.N_VERSE = {2}
                and I.N_WORD = {3}
                and I.ID_INTERL = '{4}'
                and L.ID_STRONGS = '{5}'
            ;""".format(l_pcBookId, l_pcChapter, l_pcVerse, l_pcWordId, l_pcInterlinearId, l_pcIdStrongs)

    g_loggerWord.debug('l_query {0}'.format(l_query))
    try:
        l_cursor = l_dbConnection.cursor(buffered=True)
        l_cursor.execute(l_query)

        l_wordCount = l_cursor.rowcount

        if l_wordCount == 0:
            return get_user_string(p_context, 'e_noWord').format(p_context['d']), p_context, 'Error'

        for l_groundRoot, l_translitRoot, l_idRootByte,  l_translit, l_ground, l_type, l_defShort, l_def, \
                l_derivation, l_usage, l_freqA, l_freqB, l_dict, l_dictImage, l_groundWord, l_translitWord, \
                l_translation, l_grammar, l_grammarLong, l_wordImg in l_cursor:

            l_idRoot = l_idRootByte.decode('utf-8') if l_idRootByte is not None else None

            # window title
            l_title = '{0}[{1}]-{2}'.format(
                l_translit,
                'Hb' if is_Hebrew(l_ground) else 'Gr' if is_Greek(l_ground) else 'Ar',
                ec_app_params.g_appTitle)

            # create links from ground text words inside derivation field, e.g.: אָבִיב (H24)
            l_derivation = re.sub(r'([\u0590-\u05FF\u200D][\s\u0590-\u05FF\u200D]+)\s+\((H[0-9]+)\)',
                                  r'<a href="" class="GoWord" wordId="_-_-\2"><span class="Hb">\1</span></a>',
                                  l_derivation)

            l_derivation = re.sub(r'([\u0370-\u03FF\u1F00-\u1FFF][\s\u0370-\u03FF\u1F00-\u1FFF]+)\s+\((G[0-9]+)\)',
                                  r'<a href="" class="GoWord" wordId="_-_-\2"><span class="Gk">\1</span></a>',
                                  l_derivation)

            # ensure all strongs numbers in links have 4 digits
            l_derivation = re.sub(r'<a href="" class="GoWord" wordId="_-_-([HG])([0-9]{3})">',
                                  r'<a href="" class="GoWord" wordId="_-_-\g<1>0\2">', l_derivation)
            l_derivation = re.sub(r'<a href="" class="GoWord" wordId="_-_-([HG])([0-9]{2})">',
                                  r'<a href="" class="GoWord" wordId="_-_-\g<1>00\2">', l_derivation)
            l_derivation = re.sub(r'<a href="" class="GoWord" wordId="_-_-([HG])([0-9])">',
                                  r'<a href="" class="GoWord" wordId="_-_-\g<1>000\2">', l_derivation)

            l_freqA = l_freqA.strip()
            l_freqB = l_freqB.strip()

            # Rowspan calculations ++++++++
            l_rowspan = 1
            if len(l_freqA) > 0:
                l_rowspan += 1
            if len(l_freqB) > 0:
                l_rowspan += 1
                
            if l_idGroup0 == 'FT':
                if l_pcWordId != '_':
                    # grammar box + grammar long
                    l_rowspan += 2
            else:
                # derivation & definition
                l_rowspan += 2

            if l_groundRoot is not None:
                # presence of a root field
                l_rowspan += 1

            # FIELDS ++++++++
            # meaning field to be put under the word ground text if available
            if len(l_defShort) > 0:
                l_meaning = '<div class="wMeaning">‟{0}”</div>'.format(l_defShort)
            else:
                l_meaning = ''

            # word ground text in upper left cell
            l_response += ('<tr><td rowspan="{3}" class="wGroundCell">' +
                           '<div class="{0}">{1}</div>' +
                           '<div class="wTranslit">{2}</div>{4}</td>\n').format(
                l_groundStyle, l_ground, l_translit, l_rowspan, l_meaning)

            # grammatical word type
            l_response += '<td colspan="3"><span class="pFieldName">{1}:</span> {0}</td></tr>'.format(
                l_type, get_user_string(p_context, 'w_type'))

            # root field (if any)
            if l_groundRoot is not None:
                if l_pcIdStrongs[0:1] == 'G':
                    l_groundRoot = '<span class="Gk">{0}</span>'.format(l_groundRoot)
                elif l_pcIdStrongs[0:1] == 'H':
                    l_groundRoot = '<span class="Hb">{0}</span>'.format(l_groundRoot)
                else:
                    l_groundRoot = '<span class="at">{0}</span>'.format(l_groundRoot)

                l_response += ('<tr><td colspan="3"><span class="pFieldName">{2}:</span> ' +
                               '<a href="" class="GoRoot" p_idroot="{3}">{0}</a> ' +
                               '(<span class="wTranslit">{1}</span>)</td></tr>').format(
                    l_groundRoot, l_translitRoot, get_user_string(p_context, 'w_root'), l_idRoot)

            if l_idGroup0 != 'FT':
                # derivation (etymology)
                l_response += '<tr><td colspan="3"><span class="pFieldName">{1}:</span> {0}</td></tr>'.format(
                    l_derivation, get_user_string(p_context, 'w_derivation'))
                # definition
                l_response += '<tr><td colspan="3"><span class="pFieldName">{1}:</span> {0}</td></tr>'.format(
                    l_def, get_user_string(p_context, 'w_definition'))

            # word frequency field A
            if len(l_freqA) > 0:
                l_response += '<tr><td colspan="3"><span class="pFieldName">{1}:</span> {0}</td></tr>'.format(
                    l_freqA,
                    get_user_string(p_context, 'w_freqABible') if l_idGroup0 != 'FT'
                    else get_user_string(p_context, 'w_freqAQuran'))

            # word frequency field B
            if len(l_freqB) > 0:
                l_response += '<tr><td colspan="3"><span class="pFieldName">{1}:</span> {0}</td></tr>'.format(
                    l_freqB,
                    get_user_string(p_context, 'w_freqBBible') if l_idGroup0 != 'FT'
                    else get_user_string(p_context, 'w_freqBQuran'))

            if l_idGroup0 == 'FT':
                if l_pcWordId != '_':
                    # word img with grammatical analysis (Quran only in practice)
                    if len(l_wordImg) > 0:
                        l_imgPath = '<img class="wGrammarImg" src=".{0}"/>'.format(l_wordImg)
                    else:
                        l_imgPath = ''

                    # grammar box
                    l_verseRef = '({0} {1}:{2}.{3})'.format(
                        l_chapterShortFr if l_uiLanguage == 'fr' else l_chapterShortEn,
                        l_pcChapter, l_pcVerse, l_pcWordId)

                    l_response += ('<tr><td class="wGrammarBox" colspan="3">' +
                                   '<div class="wVerseRef">{4}</div>' +
                                   '<table id="wInterlinear">' +
                                   '<tr><td class="{3}">{0}</td></tr>' +
                                   '<tr><td class="wTranslitWord">{1}</td></tr>' +
                                   '<tr><td>{2}</td></tr>' +
                                   '</table>' +
                                   l_imgPath +
                                   '<div class="wGrammar">{5}</div>' +
                                   '</td></tr>').format(
                        l_groundWord, l_translitWord, l_translation, l_groundStyle, l_verseRef, l_grammar)
                    #        {0}             {1}            {2}            {3}           {4}        {5}

                    # grammar long box
                    l_response += '<tr><td colspan="3"><span class="pFieldName">{1}:</span> {0}</td></tr>'.format(
                        l_grammarLong, get_user_string(p_context, 'w_grammarLong'))

        l_cursor.close()
    except Exception as l_exception:
        g_loggerWord.warning('Something went wrong {0}'.format(l_exception.args))

    # -------------------- List of occurences --------------------------------------------------------------------------
    l_occuVersion, l_occuCount, l_occuString = getOccurences(p_context, l_dbConnection, l_pcIdStrongs, l_pcWordId)

    # top title box with gray background
    l_response += '<tr><td colspan="4" class="wOccurencesTitle">{2} {0}{1}</td></tr>\n'.format(
       get_user_string(p_context, 'w_OccurencesTitle'), l_occuVersion, l_occuCount)

    l_response += l_occuString

    # -------------------- End -----------------------------------------------------------------------------------------
    l_response += '</table>'

    p_dbConnectionPool.releaseConnection(l_dbConnection)

    return l_response, p_context, l_title


# List of Occurences ---------------------------------------------------------------------------------------------------
def getOccurences(p_context, p_dbConnection, p_idStrongs, p_wordId=None):
    l_occuString = ''
    l_occuCount = 0

    l_uiLanguage = p_context['z']

    if p_wordId is not None:
        # called from Word, with a non '_' word ID
        l_pcBookId = g_bookAlias[p_context['b'].lower().strip()]
        l_pcChapter = p_context['c']
        l_pcVerse = p_context['v']
    else:
        # called from Root or from Word with a '_' word ID
        l_pcBookId = None
        l_pcChapter = None
        l_pcVerse = None

    if p_idStrongs[0:1] == 'G':
        l_interlList = '"L", "H"'
        l_occuVersion = ' (LXX, Bible Hub)'
    elif p_idStrongs[0:1] == 'H':
        l_interlList = '"H"'
        l_occuVersion = ' (Bible Hub)'
    else:
        l_interlList = '"C"'
        l_occuVersion = ''

    l_HorK = 'H'

    # substitute KJV instead of Bible Hub if no words with this Strong's ID in Bible Hub interlinear
    if re.search('"H"', l_interlList) is not None:
        l_query = """
            select ID_INTERL, COUNT
            from TB_INTERLINEAR_COUNT
            where
                ID_STRONGS = '{0}'
                and ID_INTERL in ({1})
        ;""".format(p_idStrongs, l_interlList)

        g_loggerWord.debug('l_query {0}'.format(l_query))
        try:
            l_cursor = p_dbConnection.cursor(buffered=True)
            l_cursor.execute(l_query)

            if l_cursor.rowcount == 0:
                l_interlList = re.sub('"H"', '"K"', l_interlList)
                l_occuVersion = re.sub('Bible Hub', 'KJV/NASB', l_occuVersion)
                l_HorK = 'K'

            l_cursor.close()
        except Exception as l_exception:
            g_loggerWord.warning('Something went wrong {0}'.format(l_exception.args))

    # get a pre-count of the occurences in order to set the limit
    l_query = """
        select ID_INTERL, COUNT
        from TB_INTERLINEAR_COUNT
        where
            ID_STRONGS = '{0}'
            and ID_INTERL in ({1})
    ;""".format(p_idStrongs, l_interlList)

    g_loggerWord.debug('l_query {0}'.format(l_query))
    try:
        l_cursor = p_dbConnection.cursor(buffered=True)
        l_cursor.execute(l_query)

        for l_interl, l_count in l_cursor:
            l_occuCount += l_count

        l_cursor.close()
    except Exception as l_exception:
        g_loggerWord.warning('Something went wrong {0}'.format(l_exception.args))

    # limit on the number of occurences displayed
    # Command = 'W'/'R' ---> soft (small) limit
    # Command = 'Wa'/'Ra' ---> hard (absolute maximum, large) limit
    if p_context['K'] == 'W' or p_context['K'] == 'R':
        l_occuLimit = ec_app_params.g_softLimit
        # the wDisplayAll link will trigger a 'Wa'/'Ra' command with otherwise the same parameters as the original
        # 'W'/'R' command
        if l_occuCount > l_occuLimit:
            l_occuString += ('<tr><td colspan="4" class="wOccurencesMsg">' +
                             '<span class="wLimitMessage">' +
                             get_user_string(p_context, 'w_limitMessage').format(
                                 ec_app_params.g_softLimit, ec_app_params.g_hardLimit) +
                             '</span> <a href="" class="wDisplayAll" command="{0}a">'.format(p_context['K']) +
                             get_user_string(p_context, 'w_displayAll') +
                             '</a></td></tr>')
    else:
        l_occuLimit = ec_app_params.g_hardLimit
        if l_occuCount > l_occuLimit:
            l_occuString += ('<tr><td colspan="4" class="wOccurencesMsg">' +
                             '<span class="wLimitMessage">' +
                             get_user_string(p_context, 'w_hardLimitMessage').format(ec_app_params.g_hardLimit) +
                             '</span></td></tr>')

    # list of all occurences
    l_query = """
        select
            I.ST_GROUND
            , I.ST_TRANSLIT
            , I.ID_BOOK
            , I.N_CHAPTER
            , I.N_VERSE
            , I.N_WORD
            , I.TX_NEIGHBORHOOD
        from
            V_INTERLINEAR I join TB_BOOK B on B.ID_BOOK = I.ID_BOOK
        where
            I.ID_STRONGS = '{0}'
            and I.ID_INTERL in ({1})
        order by
            I.ID_INTERL desc
            , B.N_ORDER
            , I.N_CHAPTER
            , I.N_VERSE
            , I.N_WORD
        limit 0, {2}
    ;""".format(p_idStrongs, l_interlList, l_occuLimit)

    g_loggerWord.debug('l_query {0}'.format(l_query))
    try:
        l_cursor = p_dbConnection.cursor(buffered=True)
        l_cursor.execute(l_query)

        for l_ground, l_translit, l_bookId, l_chapter, l_verse, l_word, l_neighborhood in l_cursor:
            # chapter info for this occurence
            l_bibleQuran, l_idGroup0, l_idGroup1, l_bookPrev, l_bookNext, l_chapterShortEn, l_chapterShortFr = \
                    g_bookChapter[l_bookId][0]

            # l_interlLocal: id of the interlinear version used for this occurence
            if p_idStrongs[0:1] == 'G':
                l_groundStyle = 'wGroundGreek'
                if l_idGroup0 == 'OT':
                    # LXX for Greek words in OT books
                    l_interlLocal = 'L'
                else:
                    # Greek words in NT
                    l_interlLocal = l_HorK
            elif p_idStrongs[0:1] == 'H':
                # Hebrew words
                l_interlLocal = l_HorK
                l_groundStyle = 'wGroundHebrew'
            else:
                # Arabic words
                l_interlLocal = 'C'
                l_groundStyle = 'wGroundArabic'

            # &nbsp; instead of spaces
            l_chapterShortEn = re.sub('\s+', '&nbsp;', l_chapterShortEn)
            l_chapterShortFr = re.sub('\s+', '&nbsp;', l_chapterShortFr)

            # Highlight the current word in the list
            if p_wordId is not None \
                    and l_bookId == l_pcBookId \
                    and str(l_chapter) == l_pcChapter \
                    and str(l_verse) == l_pcVerse \
                    and str(l_word) == str(p_wordId):
                l_cellStyle = 'wOccurencesHigh'
            else:
                l_cellStyle = 'wOccurences'

            l_occuString += '<tr><td colspan="2" class="{0}">'.format(l_cellStyle)
            # verse/word reference
            l_occuString += \
                ('(<a href="" class="GoOneVerse" pBook="{1}" pChapter="{2}" pVerse="{3}">{0}&nbsp;{2}:{3}</a>.' +
                 '<a href="" class="GoOneWord" p_book="{1}" p_chapter="{2}" p_verse="{3}" p_wordId="{5}"' +
                 '>{4}</a>)</td>').format(
                    l_chapterShortFr if l_uiLanguage == 'fr' else l_chapterShortEn,
                    l_bookId,
                    l_chapter,
                    l_verse,
                    l_word+1,
                    str(l_word) + '-' + l_interlLocal + '-' + p_idStrongs
                )
            # ground text + transliteration (if any)
            l_occuString += ('<td class="{3}"><span class="{2}">{0}</span>&nbsp;' +
                             '<span class="wTranslit">{1}</span></td>').format(
                l_ground,
                l_translit,
                l_groundStyle,
                l_cellStyle
            )

            # Neighborhood
            l_neighborhood = re.sub(r'&nbsp;\|', '&nbsp;<span class="neighborSep">|</span>', l_neighborhood)
            l_occuString += '<td class="{0}"><span class="TranslationText">{1}</span></td></tr>'.format(
                l_cellStyle, l_neighborhood)

        l_cursor.close()
    except Exception as l_exception:
        g_loggerWord.warning('Something went wrong {0}'.format(l_exception.args))

    return l_occuVersion, l_occuCount, l_occuString
