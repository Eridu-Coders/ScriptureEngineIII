# -*- coding: utf-8 -*-

import logging
import mysql.connector
import re
from string import Template

from ec_app_params import *

__author__ = 'fi11222'

# ------------------------- Logger -------------------------------------------------------------------------------------
g_loggerUtilities = logging.getLogger(g_appName + '.utilities')
if g_verboseModeOn:
    g_loggerUtilities.setLevel(logging.INFO)
if g_debugModeOn:
    g_loggerUtilities.setLevel(logging.DEBUG)

# ------------------------- Parameters hexadecimal bit masks -----------------------------------------------------------
# Single Verse Display options
g_svAllVersions = 0x001      # Display all versions (1) or only selected versions (0)
g_svDisplayLxx = 0x002       # Display interlinear LXX (1) for OT verses or not (0)
g_svDisplayKjv = 0x004       # Display KJV interlinear (1) for OT & NT verses or not (0)
g_svDisplayNasb = 0x008      # Display NASB interlinear (1) for OT & NT verses or not (0)

# Passage Display options
g_pDisplayGround = 0x010     # Display ground text (1) or not (0)
g_pParallel = 0x020          # Display versions in parallel (1) or in succession (0)


# ------------------------- Customized template class ------------------------------------------------------------------
class EcTemplate(Template):
    delimiter = '§'

# ------------------------- Version ID lists (Called at App Init) ------------------------------------------------------
g_bibleVersionId = []       # l_versionId, l_language, l_default, l_labelShort, l_labelTiny for Bible versions
g_quranVersionId = []       # l_versionId, l_language, l_default, l_labelShort, l_labelTiny for Quran versions

g_defaultBibleId = '1'      # Hexadecimal bit mask representation of the default Bible version ID
g_defaultQuranId = '1'      # same for Quran
# these serve as default values for p_context['l'] and p_context['q'] respectively


# helper function to avoid accessing global variables outside of their file
def getVersionList(p_bibleQuran='B'):
    if p_bibleQuran == 'B':
        return g_bibleVersionId
    else:
        return g_quranVersionId


# loads the version vectors from the database (performed at app startup)
def init_versions():
    global g_bibleVersionId
    global g_quranVersionId
    global g_defaultBibleId
    global g_defaultQuranId

    # this is necessary because the connection pool has not yet been initialized
    l_connector = mysql.connector.connect(
                    user=g_dbUser, password=g_dbPassword,
                    host=g_dbServer,
                    database=g_dbDatabase)

    # all versions except ground text
    l_query = """
        select
            ID_VERSION
            , FL_BIBLE_QURAN
            , ID_LANGUAGE
            , FL_DEFAULT
            , ST_LABEL_SHORT
            , ST_LABEL_TINY
        from TB_VERSION
        where ID_VERSION <> '_gr'
        order by N_ORDER
        ;"""

    g_loggerUtilities.debug('l_query: {0}'.format(l_query))

    l_cursor = l_connector.cursor(buffered=True)
    l_cursor.execute(l_query)

    # binary mask variables used to set the value of g_defaultBibleId and g_defaultQuranId
    # they are multiplied by 2 (i.e. set to next bit) each time a Bible (resp. Quran) verse is encountered
    l_maskBible = 1
    l_maskQuran = 1

    # cursor iteration
    for l_versionId, l_bq, l_language, l_default, l_labelShort, l_labelTiny in l_cursor:
        if l_bq == 'B':
            g_bibleVersionId.append((l_versionId, l_language, l_default, l_labelShort, l_labelTiny))

            if l_default == 'Y':
                # the slice is necessary because the output of hex() starts with '0x'
                g_defaultBibleId = hex(l_maskBible)[2:].upper()

            l_maskBible *= 2
        else:
            g_quranVersionId.append((l_versionId, l_language, l_default, l_labelShort, l_labelTiny))

            if l_default == 'Y':
                # the slice is necessary because the output of hex() starts with '0x'
                g_defaultQuranId = hex(l_maskQuran)[2:].upper()

            l_maskQuran *= 2

    l_cursor.close()

    g_loggerUtilities.debug('g_bibleVersionId: {0}'.format(g_bibleVersionId))
    g_loggerUtilities.debug('g_quranVersionId: {0}'.format(g_quranVersionId))

    l_connector.close()

# ------------------------- Book/Chapter data (Called at App Init) -----------------------------------------------------
g_bookChapter = {}


# g_bookChapter['id'] = [(l_bibleQuran, l_idGroup0, l_idGroup1, l_bookPrev, l_bookNext), v1, v2, ... ,vn]
#                        ^ first item in the list = tuple containing                     |<----------->|
#                          various info about the chapter                                 see below
#
# v1, v2, ... ,vn = verse count for each chapter of the book (n = number of chapters for this book)
#
# Therefore: Verse count for a given chapter = g_bookChapter['id'][chapter number]
#            Chapter count for the book = len(g_bookChapter['id']) - 1

def init_book_chapter():
    global g_bookChapter

    # this is necessary because the connection pool has not yet been initialized
    l_connector = mysql.connector.connect(
                    user=g_dbUser, password=g_dbPassword,
                    host=g_dbServer,
                    database=g_dbDatabase)

    # All books
    l_query = """
        select
            ID_BOOK
            , FL_BIBLE_QURAN
            , ID_GROUP_0
            , ID_GROUP_1
            , ID_BOOK_PREV
            , ID_BOOK_NEXT
            , ST_NAME_EN_SHORT2
            , ST_NAME_FR_SHORT2
        from TB_BOOK
        order by N_ORDER
        ;"""

    g_loggerUtilities.debug('l_query: {0}'.format(l_query))

    l_cursor = l_connector.cursor(buffered=True)
    l_cursor.execute(l_query)

    # loads the first term of each g_bookChapter['id']
    for l_bookId, l_bibleQuran, l_idGroup0, l_idGroup1, l_bookPrev, l_bookNext, l_nameEn, l_nameFr in l_cursor:
        g_bookChapter[l_bookId] = \
            [(l_bibleQuran, l_idGroup0, l_idGroup1, l_bookPrev, l_bookNext, l_nameEn, l_nameFr)]

    l_cursor.close()

    # All chapters
    l_query = """
        select ID_BOOK, N_VERSE_COUNT
        from TB_CHAPTER
        order by ST_ORDER
        ;"""

    g_loggerUtilities.debug('l_query: {0}'.format(l_query))

    l_cursor = l_connector.cursor(buffered=True)
    l_cursor.execute(l_query)

    # loads the chapter verse count terms of each g_bookChapter['id'] (from position 1 in the list onwards)
    for l_bookId, l_verseCount in l_cursor:
        g_bookChapter[l_bookId].append(l_verseCount)

    l_cursor.close()

    l_connector.close()

    g_loggerUtilities.debug('g_bookChapter: {0}'.format(g_bookChapter))


# ------------------------- Book Aliases table (Called at App Init) ----------------------------------------------------
g_bookAlias = {}    # Dictionary giving the correct book ID from one of its allowed aliases (rm, rom, ... --> Rom)


def init_book_alias():
    global g_bookAlias

    l_connector = mysql.connector.connect(
                    user=g_dbUser, password=g_dbPassword,
                    host=g_dbServer,
                    database=g_dbDatabase)

    l_query = """
        select
            ID_BOOK
            , ID_BOOK_ALIAS
        from TB_BOOKS_ALIAS
        ;"""

    g_loggerUtilities.debug('l_query: {0}'.format(l_query))

    l_cursor = l_connector.cursor(buffered=True)
    l_cursor.execute(l_query)

    for l_bookId, l_bookAliasBytes in l_cursor:
        l_bookAlias = l_bookAliasBytes.decode('utf-8')
        g_bookAlias[l_bookAlias] = l_bookId

    l_cursor.close()

    g_loggerUtilities.info('g_bookAlias loaded. Size: {0}'.format(len(g_bookAlias)))


# ------------------------- Version vector------------------------------------------------------------------------------
# creates a string of the form "id1", "id2", ..., "idn" where the ids correspond to the selected versions
# indicated by p_context['l'] (Bible) or p_context['q'] (Quran) depending on the value of p_context['b'] (book)
# used to fill in the IN clauses of the SQL requests which filter versions

def get_version_vector(p_context, p_forceAll=False):
    global g_bibleVersionId
    global g_quranVersionId

    # Get the correct book name (assumes p_context['b'] belongs to g_bookAlias keys --> must have been checked before)
    l_pcBookId = g_bookAlias[p_context['b'].lower().strip()]

    if p_forceAll:
        if l_pcBookId == 'Qur':
            l_versionList = g_quranVersionId
        else:
            l_versionList = g_bibleVersionId

        # the version Id is the first element (0th) of the tuple for each version
        l_vector = '"' + '", "'.join([v[0] for v in l_versionList]) + '"'
    else:
        l_vector = '"' + '", "'.join([v[0] for v in get_version_list(p_context)]) + '"'

    g_loggerUtilities.debug('l_vector: {0}'.format(l_vector))

    return l_vector


# ------------------------- Version dictionary -------------------------------------------------------------------------
# Same as above but the return value is a list of tuples instead of a string
# Each tuple is of the form (l_versionId, l_language, l_default, l_labelShort, l_labelTiny)
#
# p_context['q'] and p_context['l'] are hexadecimal bit vector representations of the selected versions
# (resp. Quran and Bible). E.g. p_context['q'] = 1B = 11011 --> versions 1, 2, 4 and 5 are selected

def get_version_list(p_context, p_QuranAndBible=False, p_forceBibleQuran=None):
    # if p_QuranAndBible = True --> get both versions from the Bible and Quran
    # otherwise decide based on p_context['b'] or p_forceBibleQuran if set

    global g_bibleVersionId
    global g_quranVersionId

    # Get the correct book name (assumes p_context['b'] belongs to g_bookAlias keys --> must have been checked before)
    l_pcBookId = g_bookAlias[p_context['b'].lower().strip()]

    if p_QuranAndBible:
        return get_vl_internal(g_quranVersionId, p_context['q']) + get_vl_internal(g_bibleVersionId, p_context['l'])
    else:
        # decision to return Bible or Quran version based on context (l_pcBookId) or p_forceBibleQuran if set
        l_bibleQuran = p_forceBibleQuran if p_forceBibleQuran is not None else l_pcBookId
        if l_bibleQuran[0:1] == 'Q':
            return get_vl_internal(g_quranVersionId, p_context['q'])
        else:
            return get_vl_internal(g_bibleVersionId, p_context['l'])


# internal function doing the heavy lifting
def get_vl_internal(p_versionList, p_versionWordStr):
    l_versionWord = int(p_versionWordStr, 16)
    g_loggerUtilities.debug('l_versionWord]: {0}'.format(l_versionWord))

    # list based on the binary value of the parameter p_versionWordStr
    l_list = []
    for i in range(0, len(p_versionList)):
        if l_versionWord % 2 == 1:
            l_list.append(p_versionList[i])

        l_versionWord //= 2
        if l_versionWord == 0:
            break

    # default value if list is empty
    if len(l_list) == 0:
        for l_version in p_versionList:
            if l_version[2] == 'Y':
                l_list.append(l_version)

    # last resort default value: first element in the list
    if len(l_list) == 0 and len(p_versionList) > 0:
        l_list.append(p_versionList[0])

    g_loggerUtilities.debug('l_list: {0}'.format(l_list))

    return l_list


# ------------------------- Access to i18n strings ---------------------------------------------------------------------
def get_user_string(p_context, p_stringId):
    # p_context['z'] = UI language
    # g_userStrings = dict of strings defined in ec_app_params.py.
    return g_userStrings[p_context['z'] + '-' + p_stringId]


# ------------------------- Context preprocessing ----------------------------------------------------------------------
def preprocess_context(p_context, p_previousContext):
    l_context = p_context

    # Minimal parameter presence ------------------
    l_paramVector = ['b', 'c', 'v', 'w', 'q', 'l', 'p', 'd', 's', 'o', 'e', 'h', 'i', 'j']
    for l_paramName in l_paramVector:
        if l_paramName not in l_context.keys():
            if l_paramName in p_previousContext.keys():
                l_context[l_paramName] = p_previousContext[l_paramName]
            else:
                l_context[l_paramName] = ''

    # Minimal parameter presence ------------------
    # specific values
    if l_context['b'] == '':
        l_context['b'] = 'Gen'
    if l_context['c'] == '':
        l_context['c'] = '1'
    if l_context['v'] == '':
        l_context['v'] = '1'
    if l_context['w'] == '':
        l_context['w'] = '1'
    if l_context['p'] == '':
        l_context['p'] = '0'
    if l_context['e'] == '':
        l_context['e'] = '0'
    if l_context['h'] == '':
        l_context['h'] = '0'
    if l_context['i'] == '':
        l_context['i'] = '0'
    if l_context['j'] == '':
        l_context['j'] = '0'

    # Minimal parameter presence ------------------
    # special checkbox case
    l_flagVector = ['t', 'u']
    for l_flagName in l_flagVector:
        if l_flagName not in l_context.keys():
            l_context[l_flagName] = ''

    # for 'K' (command), the default value is 'T' (table of contents)
    # for all others it is ''
    if 'K' not in l_context.keys():
        if 'K' in p_previousContext.keys():
            l_context['K'] = p_previousContext['K']
        else:
            l_context['K'] = 'T'

    # Bible/Quran default versions -------------------------
    try:
        l_bibleVersionsInt = int(l_context['l'], 16)
    except ValueError:
        l_bibleVersionsInt = int(g_defaultBibleId, 16)
        l_context['l'] = g_defaultBibleId

    try:
        l_quranVersionsInt = int(l_context['q'], 16)
    except ValueError:
        l_quranVersionsInt = int(g_defaultQuranId, 16)
        l_context['q'] = g_defaultQuranId

    if l_bibleVersionsInt >= 2 ** len(g_bibleVersionId):
        l_context['l'] = g_defaultBibleId

    if l_quranVersionsInt >= 2 ** len(g_quranVersionId):
        l_context['q'] = g_defaultQuranId

    # Search combo default values -------------------------
    # search mode
    if l_context['e'] != '0' \
            and l_context['e'] != '1' \
            and l_context['e'] != '2':
        l_context['e'] = '0'

    # Scope - Quran
    if l_context['h'] != '0' \
            and l_context['h'] != '1':
        l_context['h'] = '0'

    # Scope - NT
    if l_context['i'] != '0' \
            and l_context['i'] != '1' \
            and l_context['i'] != '2' \
            and l_context['i'] != '3' \
            and l_context['i'] != '4':
        l_context['i'] = '0'

    # Scope - OT
    if l_context['j'] != '0' \
            and l_context['j'] != '1' \
            and l_context['j'] != '2' \
            and l_context['j'] != '3' \
            and l_context['j'] != '4' \
            and l_context['j'] != '5':
        l_context['j'] = '0'

    # Parameter expansion -------------------------
    # expands the hexadecimal l_context['p'] bit mask into individual parameters
    l_paramVector = ['a', 'x', 'k', 'n', 'g', 'r']

    try:
        l_paramInt = int(l_context['p'], 16)
    except ValueError:
        l_paramInt = 0
        l_context['p'] = '0'

    for l_paramName in l_paramVector:
        l_context[l_paramName] = 0 if l_paramInt % 2 == 0 else 1
        l_paramInt //= 2

    return l_context


# ---------------- Trapping of passage references ----------------------------------------------------------------------
# Captures passage, book and verse references given in the search box
# No control is done here only trapping the probable reference values ---> proper control is done later, at the
# command handling module level
def trap_references(p_context):
    global g_bookAlias

    l_context = p_context

    # only if the current command is Search
    if p_context['K'] == 'S':
        l_searchQuery = p_context['s'].strip().lower()
        g_loggerUtilities.debug('l_searchQuery: {0}'.format(l_searchQuery))

        # All 3 Quran traps below just add 'qur' in front so that the normal trapping mechanisms can catch them
        # afterwards

        # 1) Quran passage of the form: xxx:yyy-zzz --> qur xxx:yyy-zzz
        l_match = re.search('^(\d+)[: ](\d+)-(\d+)$', l_searchQuery)
        if l_match is not None:
            l_chapter = l_match.groups()[0]
            l_verse1 = l_match.groups()[1]
            l_verse2 = l_match.groups()[2]

            g_loggerUtilities.info('Quran passage reference trapped')
            g_loggerUtilities.info('l_chapter: {0}'.format(l_chapter))
            g_loggerUtilities.info('l_verse1:  {0}'.format(l_verse1))
            g_loggerUtilities.info('l_verse2:  {0}'.format(l_verse2))

            l_searchQuery = 'qur {0}:{1}-{2}'.format(l_chapter, l_verse1, l_verse2)
            l_context['s'] = l_searchQuery

        # 2) Quran verse of the form: xxx:yyy --> qur xxx:yyy
        l_match = re.search('^(\d+)[: ](\d+)$', l_searchQuery)
        if l_match is not None:
            l_chapter = l_match.groups()[0]
            l_verse1 = l_match.groups()[1]

            g_loggerUtilities.info('Quran verse reference trapped')
            g_loggerUtilities.info('l_chapter: {0}'.format(l_chapter))
            g_loggerUtilities.info('l_verse1:  {0}'.format(l_verse1))

            l_searchQuery = 'qur {0}:{1}'.format(l_chapter, l_verse1)
            l_context['s'] = l_searchQuery

        # 3) Quran chapter of the form: xxx --> qur xxx
        l_match = re.search('^(\d+)$', l_searchQuery)
        if l_match is not None:
            l_chapter = l_match.groups()[0]

            g_loggerUtilities.info('Quran chapter reference trapped')
            g_loggerUtilities.info('l_chapter: {0}'.format(l_chapter))

            l_searchQuery = 'qur {0}'.format(l_chapter)
            l_context['s'] = l_searchQuery

        # General passage trap: xxx:yyy-zzz ---> transformed into a 'P' command
        l_match = re.search('^(\d*)\s*([a-z]+)\.?\s+(\d+)[: ](\d+)-(\d+)$', l_searchQuery)
        if l_match is not None:
            l_book = l_match.groups()[0] + l_match.groups()[1]
            l_chapter = l_match.groups()[2]
            l_verse1 = l_match.groups()[3]
            l_verse2 = l_match.groups()[4]

            g_loggerUtilities.info('Passage reference trapped')
            g_loggerUtilities.info('l_book:    {0}'.format(l_book))
            g_loggerUtilities.info('l_chapter: {0}'.format(l_chapter))
            g_loggerUtilities.info('l_verse1:  {0}'.format(l_verse1))
            g_loggerUtilities.info('l_verse2:  {0}'.format(l_verse2))

            l_context['K'] = 'P'
            l_context['b'] = l_book
            l_context['c'] = l_chapter
            l_context['v'] = l_verse1
            l_context['w'] = l_verse2

            return l_context

        # General verse trap: xxx:yyy ---> transformed into a 'V' command
        l_match = re.search('^(\d*)\s*([a-z]+)\.?\s+(\d+)[: ](\d+)$', l_searchQuery)
        if l_match is not None:
            l_book = l_match.groups()[0] + l_match.groups()[1]
            l_chapter = l_match.groups()[2]
            l_verse = l_match.groups()[3]

            g_loggerUtilities.info('Verse reference trapped')
            g_loggerUtilities.info('l_book:    {0}'.format(l_book))
            g_loggerUtilities.info('l_chapter: {0}'.format(l_chapter))
            g_loggerUtilities.info('l_verse1:  {0}'.format(l_verse))

            l_context['K'] = 'V'
            l_context['b'] = l_book
            l_context['c'] = l_chapter
            l_context['v'] = l_verse

            return l_context

        # General chapter trap: xxx ---> transformed into a 'P' command 1-x
        l_match = re.search('^(\d*)\s*([a-z]+)\.?\s+(\d+)$', l_searchQuery)
        if l_match is not None:
            l_book = l_match.groups()[0] + l_match.groups()[1]
            l_chapter = l_match.groups()[2]

            g_loggerUtilities.info('Chapter reference trapped')
            g_loggerUtilities.info('l_book:    {0}'.format(l_book))
            g_loggerUtilities.info('l_chapter: {0}'.format(l_chapter))

            l_context['K'] = 'P'
            l_context['b'] = l_book
            l_context['c'] = l_chapter
            l_context['v'] = '1'
            l_context['w'] = 'x'

            return l_context

    return l_context


# ---------------- Parameter control -----------------------------------------------------------------------------------
# ensure correct values for the parameters needed by the passage command ('P')
# called at the beginning of get_passage()
def passage_control(p_context):
    l_book = p_context['b']
    l_chapter = p_context['c']
    l_verse1 = p_context['v']
    l_verse2 = p_context['w']

    # book must be in the alias table
    if l_book.lower().strip() not in g_bookAlias.keys():
        return get_user_string(p_context, 'e_wrongBookPassage').format(
            l_book, l_chapter, l_verse1, l_verse2)
    else:
        # Get the correct book name (assumes p_context['b'] belongs to g_bookAlias keys as checked above)
        l_pcBookId = g_bookAlias[l_book.lower().strip()]

        # chapter must be a valid number
        try:
            l_intChapter = int(l_chapter)
        except ValueError:
            return get_user_string(p_context, 'e_wrongChapterPassage').format(
                l_book, l_chapter, l_verse1, l_verse2)

        # chapter must be in the right range based on the book table
        if l_intChapter < 1 or l_intChapter > len(g_bookChapter[l_pcBookId]) - 1:
            return get_user_string(p_context, 'e_wrongChapterPassage').format(
                l_book, l_chapter, l_verse1, l_verse2)
        else:
            # verse1 must be a valid number
            try:
                l_intVerse1 = int(l_verse1)
            except ValueError:
                return get_user_string(p_context, 'e_wrongV1Passage').format(
                    l_book, l_chapter, l_verse1, l_verse2)

            l_intVerse2 = 0
            # verse2 must be a valid number except in the case where v1 = 1 and v2 = 'x' (indicating 'whole chapter)
            try:
                l_intVerse2 = int(l_verse2)
            except ValueError:
                if not (l_intVerse1 == 1 and l_verse2 == 'x'):
                    return get_user_string(p_context, 'e_wrongV2Passage').format(
                        l_book, l_chapter, l_verse1, l_verse2)

            # v1 must be in the right range as determined based on the chapter and book
            if l_intVerse1 < 1 or l_intVerse1 > g_bookChapter[l_pcBookId][l_intChapter]:
                return get_user_string(p_context, 'e_wrongV1Passage').format(
                    l_book, l_chapter, l_verse1, l_verse2)
            # v2 must be in the same range as v1 and also greater than v1
            elif l_verse2 != 'x' and \
                    (l_intVerse2 < 1 or l_intVerse2 > g_bookChapter[l_pcBookId][l_intChapter] or
                     l_intVerse1 > l_intVerse2):
                return get_user_string(p_context, 'e_wrongV2Passage').format(
                    l_book, l_chapter, l_verse1, l_verse2)

    return ''


# ensure correct values for the parameters needed by the verse command ('V')
# called at the beginning of get_single_verse()
def verse_control(p_context):
    l_book = p_context['b']
    l_chapter = p_context['c']
    l_verse = p_context['v']

    # book must be in the alias table
    if l_book.lower().strip() not in g_bookAlias.keys():
        return get_user_string(p_context, 'e_wrongBookVerse').format(
            l_book, l_chapter, l_verse)
    else:
        # Get the correct book name (assumes p_context['b'] belongs to g_bookAlias keys as checked above)
        l_pcBookId = g_bookAlias[l_book.lower().strip()]

        # chapter must be a valid number
        try:
            l_intChapter = int(l_chapter)
        except ValueError:
            return get_user_string(p_context, 'e_wrongChapterVerse').format(
                l_book, l_chapter, l_verse)

        # chapter must be in the right range based on the book table
        if l_intChapter < 1 or l_intChapter > len(g_bookChapter[l_pcBookId]) - 1:
            return get_user_string(p_context, 'e_wrongChapterVerse').format(
                l_book, l_chapter, l_verse)
        else:
            # verse must be a valid number
            try:
                l_intVerse = int(l_verse)
            except ValueError:
                return get_user_string(p_context, 'e_wrongVVerse').format(
                    l_book, l_chapter, l_verse)

            # verse must be in the right range as determined based on the chapter and book
            if l_intVerse < 1 or l_intVerse > g_bookChapter[l_pcBookId][l_intChapter]:
                return get_user_string(p_context, 'e_wrongVVerse').format(
                    l_book, l_chapter, l_verse)

    return ''


# ensure correct values for the parameters needed by the word command ('W')
# called at the beginning of get_word()
def word_control(p_context):
    l_book = p_context['b']
    l_chapter = p_context['c']
    l_verse = p_context['v']

    # the word ID parameter must be of the form X-Y-Z9999 where
    # X is a number (Word number)
    # Y is C, H, K or L (interlinear ID)
    # Z is H, G or A (Strong's number initial)
    # 9999 is a 4 digit number
    # or the ID must be of the form _-_-Z9999 (no word ID and Interlinear ID provided)
    if re.search('([0-9]+|_)-[CHKL_]-[HGA][0-9]{4}', p_context['d']) is None:
        return get_user_string(p_context, 'e_wrongIdWord').format(
            l_book, l_chapter, l_verse, p_context['d'])

    l_wordId = p_context['d'].split('-')[0]
    l_interlinearId = p_context['d'].split('-')[1]
    l_idStrongs = p_context['d'].split('-')[2]

    # if both the word ID and the interlinear ID are '_' then there is no further test to perform
    # otherwise, all the tests below apply
    if not(l_wordId == '_' and l_interlinearId == '_'):
        # book must be in the alias table
        if l_book.lower().strip() not in g_bookAlias.keys():
            return get_user_string(p_context, 'e_wrongBookWord').format(
                l_book, l_chapter, l_verse, l_wordId, l_interlinearId, l_idStrongs)
        else:
            # Get the correct book name (assumes p_context['b'] belongs to g_bookAlias keys as checked above)
            l_pcBookId = g_bookAlias[l_book.lower().strip()]

            # chapter must be a valid number
            try:
                l_intChapter = int(l_chapter)
            except ValueError:
                return get_user_string(p_context, 'e_wrongChapterWord').format(
                    l_book, l_chapter, l_verse, l_wordId, l_interlinearId, l_idStrongs)

            # chapter must be in the right range based on the book table
            if l_intChapter < 1 or l_intChapter > len(g_bookChapter[l_pcBookId]) - 1:
                return get_user_string(p_context, 'e_wrongChapterWord').format(
                    l_book, l_chapter, l_verse, l_wordId, l_interlinearId, l_idStrongs)
            else:
                # verse must be a valid number
                try:
                    l_intVerse = int(l_verse)
                except ValueError:
                    return get_user_string(p_context, 'e_wrongVWord').format(
                        l_book, l_chapter, l_verse, l_wordId, l_interlinearId, l_idStrongs)

                # verse must be in the right range as determined based on the chapter and book
                if l_intVerse < 1 or l_intVerse > g_bookChapter[l_pcBookId][l_intChapter]:
                    return get_user_string(p_context, 'e_wrongVWord').format(
                        l_book, l_chapter, l_verse, l_wordId, l_interlinearId, l_idStrongs)
                else:
                    # word ID must be a valid number
                    try:
                        l_intWord = int(l_wordId)
                    except ValueError:
                        return get_user_string(p_context, 'e_wrongWordWord').format(
                            l_book, l_chapter, l_verse, l_wordId, l_interlinearId, l_idStrongs)

                    # word number must be in a "reasonable" range
                    if l_intWord < 1 or l_intWord > 500:
                        return get_user_string(p_context, 'e_wrongWordWord').format(
                            l_book, l_chapter, l_verse, l_wordId, l_interlinearId, l_idStrongs)

    return ''


# ensure correct values for the parameters needed by the root command ('R')
# called at the beginning of get_root()
def root_control(p_context):
    l_rootString = p_context['d']

    # the word ID parameter must be a sequence of items separated by '|'. Each item is either
    # 1) a strongs number: Z9999 with Z = A, H or G and 9999 a 4 digit number, or
    # 2) a "pure root" ID of the form X-ZZZ with ZZZ any trigram of capital letters
    if re.search('(\S{3}|[HGA][0-9]{4}|X-[A-Z]{3})(\|(\S{3}|[HGA][0-9]{4}|X-[A-Z]{3}))*', l_rootString) is None:
        return get_user_string(p_context, 'e_wrongRoot').format(l_rootString)

    return ''


# ------------------------- Chapter names (en/fr) ----------------------------------------------------------------------
# get the French and English full chapter name corresponding to context (p_context['b'] + p_context['c'])
def get_chapter_names(p_context, p_dbConnection):
    # Get the correct book name (assumes p_context['b'] belongs to g_bookAlias keys --> must have been checked before)
    l_pcBookId = g_bookAlias[p_context['b'].lower().strip()]

    l_query = """
        select ST_NAME_EN, ST_NAME_FR
        from TB_CHAPTER
        where
            ID_BOOK = '{0}'
            and N_CHAPTER = {1}
        ;""".format(l_pcBookId, p_context['c'])

    g_loggerUtilities.debug('l_query {0}'.format(l_query))
    l_chapterEn, l_chapterFr = '', ''
    try:
        l_cursor = p_dbConnection.cursor(buffered=True)
        l_cursor.execute(l_query)

        for l_chapterEn, l_chapterFr in l_cursor:
            pass

        l_cursor.close()
    except Exception as l_exception:
        g_loggerUtilities.warning('Something went wrong {0}'.format(l_exception.args))
        l_chapterEn, l_chapterFr = 'Not Found', 'Non trouvé'

    return l_chapterEn, l_chapterFr


# ------------------------- One verse translation display --------------------------------------------------------------
# Common verse formatting for search output and passages
# p_rightToLeft: for Hebrew and Arabic
# p_highlightList: list of words to highlight (search output only)
# p_highlightCaseSensitive: highlight take case into account ? (search output only)
# p_counter: number to display btw [] to the left of the verse ref (search output only)
def makeVerse(p_bookId, p_chapterNumber, p_verseNumber, p_verseText, p_bookShort, p_rightToLeft=False,
              p_highlightList=None, p_highlightCaseSensitive=False, p_counter=None):

    l_verseText = p_verseText

    # in order for highlighting to work properly, the words must have been ordered LONGEST FIRST so that the
    # 'willingly unwillingly problem does not arise'. This is done when processing the search parameters
    if p_highlightList is not None:
        for l_word in p_highlightList:
            l_word = clean_search_word(l_word)
            l_verseText = re.sub(
                '(' + l_word + ')',
                r'<b>\1</b>',
                l_verseText,
                re.IGNORECASE if not p_highlightCaseSensitive else 0)

    # proper class, depending on language
    if is_Hebrew(l_verseText):
        l_verseText = '<span class="sHebrew">{0}</span>'.format(l_verseText)
    elif is_Greek(l_verseText):
        l_verseText = '<span class="sGreek">{0}</span>'.format(l_verseText)
    elif is_Arabic(l_verseText):
        l_verseText = '<span class="sArabic">{0}</span>'.format(l_verseText)

    if p_rightToLeft:
        # for right to left display, the verse reference is put into a <div> that the CSS floats rightwards.
        # That way, the text floats around it as it should
        return ('<div class="sFloatingVerse">' +
                '<a href="" class="GoOneVerse" pBook="{0}" pChapter="{1}" pVerse="{2}">' +
                '{3} {1}:{2}</a>' +
                (' <span class="sCounter">[{0}]</span>'.format(p_counter) if p_counter is not None else '') +
                '</div>' +
                '<p class="OneVerseTranslationRL">{4}</p>').format(
                    p_bookId, p_chapterNumber, p_verseNumber, p_bookShort, l_verseText
                )
    else:
        return ('<p class="OneVerseTranslation">' +
                ('<span class="sCounter">[{0}]</span> '.format(p_counter) if p_counter is not None else '') +
                '<a href="" class="GoOneVerse" pBook="{0}" pChapter="{1}" pVerse="{2}">' +
                '{3} {1}:{2}</a> <span class="TranslationText">{4}</span></p>').format(
                    p_bookId, p_chapterNumber, p_verseNumber, p_bookShort, l_verseText
                )
    # In both cases, the verse reference is put into a link with a GoOneVerse class (+ book/chapter/verse params.)


# Neighborhood creation function ---------------------------------------------------------------------------------------
# This function is never used online (it used to be but was too slow)
# Instead, the neighborhoods are created (by this function) using the off-line script makeNeighborhoods.py
# which stores them into the TB_INTERLINEAR table.
def getNeighborhood(p_dbConnectionPool, p_interlinear, p_bookId, p_chapter, p_verse, p_wordStart, p_wordEnd, p_word):
    # p_word is used to highlight the word at the center of the neighborhood

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

    l_neighborhood = ''
    g_loggerUtilities.info('l_query {0}'.format(l_query))
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
        g_loggerUtilities.warning('Something went wrong {0}'.format(l_exception.args))

    p_dbConnectionPool.releaseConnection(l_connector)

    return l_neighborhood.strip()


# Word cleanup before use in search query ------------------------------------------------------------------------------
# If a word is in a given ancient language (Hebrew, Arabic or Greek), remove all characters not of this language
def clean_search_word(p_word):
    if is_Greek(p_word):
        # Greek [\u0370-\u03FF\u1F00-\u1FFF]
        return re.sub('[^\u0370-\u03FF\u1F00-\u1FFF]', '', p_word)
    elif is_Hebrew(p_word):
        # Hebrew [\u0590-\u05FF\u200D]
        return re.sub('[^\u0590-\u05FF\u200D]', '', p_word)
    elif is_Arabic(p_word):
        # Arabic [\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]
        return re.sub('[^\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]', '', p_word)
    else:
        return re.sub('[^ a-zA-Zéèêàâôïäëçùûʼ]', '', p_word)


def is_Greek(p_word):
    return re.search('[\u0370-\u03FF\u1F00-\u1FFF]', p_word) is not None


def is_Hebrew(p_word):
    return re.search('[\u0590-\u05FF\u200D]', p_word) is not None


def is_Arabic(p_word):
    return re.search('[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]', p_word) is not None
