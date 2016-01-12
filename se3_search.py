# -*- coding: utf-8 -*-

from se3_utilities import *

__author__ = 'fi11222'

# -------------------------- Logger ------------------------------------------------------------------------------------
g_loggerSearch = logging.getLogger(g_appName + '.search')
if g_verboseModeOn:
    g_loggerSearch.setLevel(logging.INFO)
if g_debugModeOn:
    g_loggerSearch.setLevel(logging.DEBUG)


# -------------------------- Search Result -----------------------------------------------------------------------------
def get_search(p_previousContext, p_context, p_dbConnectionPool):
    g_loggerSearch.info('Getting search response')
    g_loggerSearch.debug('p_previousContext: {0}'.format(p_previousContext))
    g_loggerSearch.debug('p_context: {0}'.format(p_context))

    l_dbConnection = p_dbConnectionPool.getConnection()
    l_response = ''

    # parameters
    l_pcSearchQuery = re.sub('\s+', ' ', p_context['s']).strip()
    l_pcExclude = re.sub('\s+', ' ', p_context['o']).strip()

    l_pcWholeWords = (p_context['t'] == 'checked')
    l_pcCaseSensitive = (p_context['u'] == 'checked')

    l_pcCommand = p_context['K']
    
    l_pcMode = p_context['e']
    l_pcScopeQuran = p_context['h']
    l_pcScopeNT = p_context['i']
    l_pcScopeOT = p_context['j']

    # window title
    l_title = l_pcSearchQuery + '-' + g_appTitle

    # limit on the number of verses displayed
    # Command = 'S' ---> soft (small) limit
    # Command = 'Sa' ---> hard (absolute maximum, large) limit
    if l_pcCommand == 'S':
        l_verseLimit = g_softLimit
    else:
        l_verseLimit = g_hardLimit

    # construct SQL query based on parameters
    # + useful byproducts:
    # l_wordList = search query broken down into a list of words
    #              (list because order matters due to 'willingly unwillingly' problem)
    # l_excludedSet = same for excluded words (set because here order does not matter)
    l_query, l_wordList, l_excludedSet = \
        internal_get_query(p_context, l_pcSearchQuery, l_pcExclude, l_pcMode, l_pcWholeWords, l_pcCaseSensitive,
                           l_pcScopeQuran, l_pcScopeNT, l_pcScopeOT)

    g_loggerSearch.debug('l_query: {0}'.format(l_query))
    # query execution
    try:
        l_cursor = l_dbConnection.cursor(buffered=True)
        l_cursor.execute(l_query)
        g_loggerSearch.info('Verse count: {0}'.format(l_cursor.rowcount))

        l_verseCount = l_cursor.rowcount

        # report message construction
        l_response += internal_get_report(p_context, l_wordList, l_pcMode, l_pcCaseSensitive, l_pcWholeWords,
                                          l_excludedSet, l_pcScopeQuran, l_pcScopeNT, l_pcScopeOT, l_verseCount)

        # display of limit message, if necessary
        if l_verseCount > g_softLimit and l_pcCommand == 'S':
            # the DisplayAll link will trigger a 'Sa' command with otherwise the same parameters as the original
            # 'S' command
            l_response += '<p class="sLimitMessage">' + \
                          get_user_string(p_context, 's_limitMessage').format(g_softLimit, g_hardLimit) + \
                          ' <a href="" class="DisplayAll">' + \
                          get_user_string(p_context, 's_displayAll') +\
                          '</a></p>'

        l_verseIndex = 0
        # list all verses  returned by the query, within the limit
        for l_bq, l_versionLabel, l_versionOrder, l_bookOrder, l_bookNameEn, l_bookNameFr, l_idGroup0, l_idGroup1, \
                l_idBook, l_chapterNumber, l_verseNumber, l_text in l_cursor:

            l_response += makeVerse(l_idBook, l_chapterNumber, l_verseNumber, l_text,
                                    l_bookNameFr if p_context['z'] == 'fr' else l_bookNameEn,
                                    p_rightToLeft=is_Hebrew(l_text) or is_Arabic(l_text),
                                    p_highlightList=l_wordList,
                                    p_highlightCaseSensitive=l_pcCaseSensitive,
                                    p_counter=l_verseIndex + 1,
                                    p_versionLabel=l_versionLabel)

            l_verseIndex += 1
            # stop if limit reached
            if l_verseIndex >= l_verseLimit:
                break

        l_cursor.close()
    except Exception as l_exception:
        g_loggerSearch.warning('Something went wrong {0}'.format(l_exception.args))

    p_dbConnectionPool.releaseConnection(l_dbConnection)

    return l_response, p_context, l_title


def internal_get_report(p_context, p_wordList, l_mode, p_caseSensitive, p_wholeWords, p_excludedSet,
                        p_scopeQuran, p_scopeNT, p_scopeOT, p_verseCount):

        # construct the message displayed at the top of the search response verse list, indicating verse count,
        # words searched for, words excluded, versions and book scope.

        # put an appropriate style on searched words if they happen to be in Arabic/Hebrew/Greek
        l_wordListStyle = []
        for l_word in p_wordList:
            if is_Arabic(l_word):
                l_wordListStyle.append('<span class="sArabic">{0}</span>'.format(l_word))
            elif is_Hebrew(l_word):
                l_wordListStyle.append('<span class="sHebrew">{0}</span>'.format(l_word))
            elif is_Greek(l_word):
                l_wordListStyle.append('<span class="sGreek">{0}</span>'.format(l_word))
            else:
                l_wordListStyle.append(l_word)

        # the representation of the search word list
        if len(p_wordList) == 1:
            l_wordSequence = '‟<b>{0}</b>”'.format(l_wordListStyle[0])
        else:
            l_wordSequence = '‟<b>' + '</b>”, ‟<b>'.join(l_wordListStyle[0:-1]) + '</b>” ' + \
                             (get_user_string(p_context, 's_and') if l_mode == '0'
                              else get_user_string(p_context, 's_or')) + \
                             ' ‟<b>{0}</b>”'.format(l_wordListStyle[-1])

        # 'the phrase' or 'the word'/'the words' depending on search mode
        if l_mode == '2':
            # exact phrase
            l_wordPhrase = get_user_string(p_context, 's_report2phrase')
        else:
            # AND or OR
            l_wordPhrase = get_user_string(p_context, 's_report2singular') if len(p_wordList) == 1 \
                else get_user_string(p_context, 's_report2plural')

        # put an appropriate style on excluded words if they happen to be in Arabic/Hebrew/Greek
        if len(p_excludedSet) > 0:
            l_listExcluded = []
            for l_word in list(p_excludedSet):
                if is_Arabic(l_word):
                    l_listExcluded.append('<span class="sArabic">{0}</span>'.format(l_word))
                elif is_Hebrew(l_word):
                    l_listExcluded.append('<span class="sHebrew">{0}</span>'.format(l_word))
                elif is_Greek(l_word):
                    l_listExcluded.append('<span class="sGreek">{0}</span>'.format(l_word))
                else:
                    l_listExcluded.append(l_word)

            # representation of the list of excluded words
            if len(p_excludedSet) == 1:
                l_excludedSequence = get_user_string(p_context, 's_report3singular') + \
                                     ' ‟<b>{0}</b>” '.format(l_listExcluded[0])
            else:
                l_excludedSequence = get_user_string(p_context, 's_report3plural') + \
                                     ' ‟<b>' + '</b>”, ‟<b>'.join(l_listExcluded[0:-1]) + '</b>” ' + \
                                     get_user_string(p_context, 's_or') + \
                                     ' ‟<b>{0}</b>” '.format(l_listExcluded[-1])
        else:
            l_excludedSequence = ''

        # representation of the list of versions
        l_versions = get_version_list(p_context, True)
        if len(l_versions) == 1:
            l_versionSequence = get_user_string(p_context, 's_report4singular') + \
                                '<i>{0}</i>'.format(l_versions[0][3])
        else:
            l_versionSequence = get_user_string(p_context, 's_report4plural') + \
                                ' <i>' + '</i>, <i>'.join(l_version[3] for l_version in l_versions[0:-1]) + '</i> ' +\
                                get_user_string(p_context, 's_and') + \
                                ' <i>{0}</i>'.format(l_versions[-1][3])

        # representation of the book scopes
        l_bookScope = ''
        if p_scopeQuran == '0':
            l_bookScope += '<b>' + get_user_string(p_context, 's_scopeQuran') + '</b> '

        if p_scopeNT == '0':
            l_bookScope += get_user_string(p_context, 's_and') + \
                           ' <b>' + get_user_string(p_context, 's_scopeNT') + '</b> '
        elif p_scopeNT == '1':
            l_bookScope += get_user_string(p_context, 's_and') + \
                           ' <b>' + get_user_string(p_context, 's_scopeNTGospelA') + '</b> '
        elif p_scopeNT == '2':
            l_bookScope += get_user_string(p_context, 's_and') + \
                           ' <b>' + get_user_string(p_context, 's_scopeNTEpi') + '</b> '
        elif p_scopeNT == '3':
            l_bookScope += get_user_string(p_context, 's_and') + \
                           ' <b>' + get_user_string(p_context, 's_scopeNTRev') + '</b> '

        if p_scopeOT == '0':
            l_bookScope += get_user_string(p_context, 's_and') + \
                           ' <b>' + get_user_string(p_context, 's_scopeOT') + '</b> '
        elif p_scopeOT == '1':
            l_bookScope += get_user_string(p_context, 's_and') + \
                           ' <b>' + get_user_string(p_context, 's_scopeOTPentateuch') + '</b> '
        elif p_scopeOT == '2':
            l_bookScope += get_user_string(p_context, 's_and') + \
                           ' <b>' + get_user_string(p_context, 's_scopeOTHist') + '</b> '
        elif p_scopeOT == '3':
            l_bookScope += get_user_string(p_context, 's_and') + \
                           ' <b>' + get_user_string(p_context, 's_scopeOTWis') + '</b> '
        elif p_scopeOT == '4':
            l_bookScope += get_user_string(p_context, 's_and') + \
                           ' <b>' + get_user_string(p_context, 's_scopeOTPro') + '</b> '

        l_bookScope = l_bookScope.strip()
        # removal of the first 'and' in the book scope representation
        l_bookScope = get_user_string(p_context, 's_scope') + ': ' + \
            re.sub('^' + get_user_string(p_context, 's_and'), '', l_bookScope).strip()

        g_loggerSearch.info('l_bookScope: {0}'.format(l_bookScope))

        # final construction of the report message
        l_report = '<p class="ResultBox"><b>{0}</b> {1} {2} {3} {4}({5}{6}) {7}. {8}</p>'.format(
            p_verseCount,
            get_user_string(p_context, 's_report1singular') if p_verseCount == 1
            else get_user_string(p_context, 's_report1plural'),
            l_wordPhrase,
            l_wordSequence,
            l_excludedSequence,
            get_user_string(p_context, 's_caseSensitive') if p_caseSensitive
            else get_user_string(p_context, 's_caseInsensitive'),
            (', ' + get_user_string(p_context, 's_wholeWords')) if p_wholeWords else '',
            l_versionSequence,
            l_bookScope
        )

        return l_report


def internal_get_query(p_context, p_searchQuery, p_exclude, p_mode, p_wholeWords, p_caseSensitive, p_scopeQuran,
                       p_scopeNT, p_scopeOT):

    # generates the SQL query which will retrieve the verses

    # generates the SQL condition for selecting the translations (in an IN clause)
    l_versions = get_version_list(p_context, True)
    if len(l_versions) > 0:
        l_versionFilter = '"' + '","'.join(l_version[0] for l_version in l_versions) + '", "_gr"'
    else:
        l_versionFilter = '"esv", "khalifa", "_gr"'
    g_loggerSearch.info('l_versionFilter: {0}'.format(l_versionFilter))

    # generates the SQL condition for selecting the book range
    l_bookFilter = ''
    if p_scopeQuran == '0' and p_scopeNT == '0' and p_scopeOT == '0':
        # all 3 scope selectors in 'All' position
        l_bookFilter = 'true'
    else:
        if p_scopeQuran == '0':
            # Quran selector in position 'All'
            l_bookFilter += 'B.ID_GROUP_0 = "FT" or '

        if p_scopeNT == '0':
            # NT selector in position 'All'
            l_bookFilter += 'B.ID_GROUP_0 = "NT" or '
        elif p_scopeNT == '1':
            # NT selector in position 'Gospel and Acts'
            l_bookFilter += 'B.ID_GROUP_1 = "GosA" or '
        elif p_scopeNT == '2':
            # NT selector in position 'Epistles'
            l_bookFilter += 'B.ID_GROUP_1 = "Epi" or '
        elif p_scopeNT == '3':
            # NT selector in position 'Revelation'
            l_bookFilter += 'B.ID_GROUP_1 = "Rev" or '

        if p_scopeOT == '0':
            # OT selector in position 'All'
            l_bookFilter += 'B.ID_GROUP_0 = "OT" or '
        elif p_scopeOT == '1':
            # OT selector in position 'Pentateuch'
            l_bookFilter += 'B.ID_GROUP_1 = "Pen" or '
        elif p_scopeOT == '2':
            # OT selector in position 'History'
            l_bookFilter += 'B.ID_GROUP_1 = "Hist" or '
        elif p_scopeOT == '3':
            # OT selector in position 'Wisdom'
            l_bookFilter += 'B.ID_GROUP_1 = "Wis" or '
        elif p_scopeOT == '4':
            # OT selector in position 'Prophets'
            l_bookFilter += 'B.ID_GROUP_1 = "Pro" or '

        # default value or final cleanup
        if len(l_bookFilter) == 0:
            l_bookFilter = 'true'
        else:
            l_bookFilter = re.sub('\sor\s$', '', l_bookFilter)

    g_loggerSearch.info('l_bookFilter: {0}'.format(l_bookFilter))

    # generate the full-text search query, i.e. the 'boolean' query in MySQL parlance
    # (and the word list as a byproduct)
    l_wordList = list()
    l_booleanQuery = ''

    l_searchQuery = re.sub('\s+', ' ', p_searchQuery)
    # to avoid the Muababamen problem
    l_searchQuery = re.sub("'", 'ʼ', l_searchQuery)
    l_searchQuery = re.sub('"', '', l_searchQuery).strip()
    g_loggerSearch.debug('l_pcSearchQuery: {0}'.format(l_searchQuery))

    l_exclude = re.sub('\s+', ' ', p_exclude)
    # to avoid the Muababamen problem
    l_exclude = re.sub("'", 'ʼ', l_exclude)
    l_exclude = re.sub('"', '', l_exclude).strip()
    g_loggerSearch.debug('l_exclude: {0}'.format(l_exclude))

    if p_mode == '2':
        # exact phrase: the boolean query is the whole search query
        l_booleanQuery = '+"{0}" '.format(clean_search_word(l_searchQuery).strip())
        l_wordList.append(l_searchQuery)
        l_wildcard = ''
    else:
        # OR or AND
        if p_mode == '0':
            # AND
            l_operator = '+'
        else:
            # OR
            l_operator = ''

        if p_wholeWords:
            # whole words
            l_wildcard = ''
        else:
            l_wildcard = '*'

        # add a boolean query term for each separate word in the search query
        for l_word in l_searchQuery.split(' '):
            if l_word in l_wordList:
                continue

            l_booleanQuery += l_operator + l_word + l_wildcard + ' '

            l_word = clean_search_word(l_word).strip()
            if len(l_word) > 0:
                l_wordList.append(l_word)

        if len(l_booleanQuery) == 0:
            l_booleanQuery = '+Aaron'
            l_wordList.append('Aaron')

    # set of excluded words
    l_excludedSet = set(l_exclude.split(' '))

    # add terms to the boolean query for the excluded words
    if len(l_exclude) > 0:
        for l_word in l_excludedSet:
            l_booleanQuery += '-' + l_word + l_wildcard + ' '

    l_booleanQuery = l_booleanQuery.strip()

    # TX_VERSE has utf-8_bin collation to make it case sensitive, TX_VERSE_INSENSITIVE has the normal
    # utf-8_general_ci collation, which is case insensitive
    if p_caseSensitive:
        l_textField = 'TX_VERSE'
    else:
        l_textField = 'TX_VERSE_INSENSITIVE'

    # reorder the word list to avoid the "willingly unwillingly" problem
    # longer words must be first so that 'unwillingly' will be bolded as '<b>unwillingly</b>' and not as
    # 'un<b>willingly</b>' in verse displays
    l_finished = False
    while not l_finished:
        i = 0
        j = 0
        try:
            for i in range(0, len(l_wordList)):
                for j in range(i+1, len(l_wordList)):
                    if re.search(l_wordList[i], l_wordList[j]):
                        l_tmp = l_wordList[i]
                        l_wordList[i] = l_wordList[j]
                        l_wordList[j] = l_tmp
                        raise NameError('Swapped')
            l_finished = True
        except NameError:
            g_loggerSearch.debug('swapped: {0} and {1}'.format(i, j))

    g_loggerSearch.debug('l_booleanQuery: {0}'.format(l_booleanQuery))
    g_loggerSearch.debug('l_wordList: {0}'.format(l_wordList))

    # final query assembly
    l_query = """
        select
            V.FL_BIBLE_QURAN
            , V.ST_LABEL_TINY
            , V.N_ORDER as N_ORDER_VERSION
            , B.N_ORDER as N_ORDER_BOOK
            , B.ST_NAME_EN_SHORT2
            , B.ST_NAME_FR_SHORT2
            , B.ID_GROUP_0
            , B.ID_GROUP_1
            , A.ID_BOOK
            , A.N_CHAPTER
            , A.N_VERSE
            , A.TX_VERSE_INSENSITIVE
        from
            (
                select *
                from TB_VERSES
                where match({3}) against( '{0}' in boolean mode ) and (ID_VERSION in ({1}))
            ) as A join
            (TB_VERSION as V, TB_BOOK  as B)
                on A.ID_VERSION = V.ID_VERSION and A.ID_BOOK = B.ID_BOOK
        where {2}
        order by B.ID_GROUP_0, B.N_ORDER, A.N_CHAPTER, A.N_VERSE, V.N_ORDER
    ;""".format(l_booleanQuery, l_versionFilter, l_bookFilter, l_textField)
    #               {0}                {1}            {2}           {3}

    return l_query, l_wordList, l_excludedSet
