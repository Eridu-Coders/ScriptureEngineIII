# -*- coding: utf-8 -*-

from ec_utilities import *

from se3_single_verse import *
from se3_passage import *
from se3_root import *
from se3_search import *
from se3_lexicon import *

__author__ = 'fi11222'

# ---------------------- Overall principles ----------------------------------------------------------------------------

# 1) At app startup, init() is called to initialize all application-specific data structures

# 2) For each request, the EC framework calls se3_entry_point() and provides it with:
# p_context: dictionary of all variables in the request string
# p_previousContext: context of the previous request that came from the same terminal (if any)
#
# se3_entry_point() returns the page to display (l_response) and the context as it modified it (because of parameter
# expansion, default values, reference trapping, etc)

# PARAMETER EXPANSION : the boolean parameters (LXX display, parallel, etc) are stored in a bit mask (p_context['p']).
# They are 'expanded' in the sense that they are transformed into a series of individual boolean values stored
# in p_context (keys : 'a', 'x', 'k', 'n', 'g', 'r')

# REFERENCE TRAPPING : passage / book / verse references given in the search box are transformed into an appropriate
# request for a verse or passage response. For example
# S 'rm 1:3-12' ---> P 'Rom', '1', '3', '12' (Book, chapter, v1, v2)
# S 'rm 1' ---> P 'Rom', '1', '1', 'x' (Book, chapter, all chapter)
# S 'rm 1:3' ---> P 'Rom', '1', '3' (Book, chapter, verse)

# Summary of commands and their parameters

# K : command

# 'R' d                     Root + list of root IDs
# 'W' (b c v) d             Word + verse ref (optional) + word ID
# 'V' b c v                 Verse + verse ref
# 'P' b c v w               Passage + Book/Chapter + v1-v2 (w = 'x' --> whole chapter)
# 'S' s t u e o h i j       Search - limit 200
# 'Sa' s t u e o h i j      Search - limit 10000

# 'T'                       Toc - all scripture
# 'Ta1'                     Toc - Quran, Surah order
# 'Ta2'                     Toc - Quran, revelation order
# 'Tb'                      Toc - NT
# 'Tc'                      Toc - OT

# s : search string
# t : whole words checkbox ('checked' if checked)
# u : case sensitive checkbox ('checked' if checked)
# e : exclude string
# o : search mode (0=AND, 1=OR, 2=Exact Phrase)
# h : quran scope (0=All, 1=No)
# i : NT scope (0=All, 1=Gospels+Acts, 2=Epistles, 3=Revelation, 4=No)
# j : OT scope (0=All, 1=Pentateuch, 2=History, 3=Wisdom, 4=Prophets, 5=No)

# p Parameters (True/False)
#        *** Single Verse ***
#    a - All versions / Selected versions
#    x - Display LXX interlinear
#    k - Display KJV interlinear
#    n - Display NASB interlinearT
#
#        *** Passage ***
#    g - Display ground text
#    r - parallel

# d : format = NNN-I-Z9999 with
#       NNN  : word number
#       I    : interlinear version ID (H, L, K or C)
#       Z    : A, H or G      | Strong's
#       9999 : 4 digit number | number

# z : UI language (given by EC framework based on accept-language)

# Parameter                                         Used by
# a - (p) All versions / Selected versions          V/P
# b - book                                          V/P/W
# c - chapter                                       V/P/W
# d - word Id                                       W/R
# e - search mode                                   S
# f
# g - (p) Display ground text                       P
# h - scope/Quran                                   S
# i - scope/NT                                      S
# j - scope/OT                                      S
# k - (p) Display KJV interlinear                   V
# l - Bible versions                                S/V/P
# m
# n - (p) Display NASB interlinear                  V
# o - exclude                                       S
# p - parameters                                    V/P
# q - Quran versions                                S/V/P
# r - (p) parallel                                  P
# s - search string                                 S
# t - whole words (''/checked)                      S
# u - case sensitive (''/checked)                   S
# v - verse (or v1)                                 V/P
# w - verse 2 (passage)                             P
# x - (p) Display LXX interlinear                   P
# y - browser capabilities test                     Request Handler
# z - UI language                                   All

# ###### required optional Python 3 packages ###############
# pytz   : sudo pip3 install pytz
# psutil : sudo pip3 install psutil
# Mysql  : sudo apt-get install python3-mysql.connector [Ubuntu >= 14.04]

# NOTE - Adding french spell-check dictionary to pyCharm:
# sudo apt-get install aspell-fr
# aspell --lang fr_FR dump master | aspell --lang fr expand | tr ' ' '\n' > french.dic
# french.dic must be in a dir by itself
# then add the french.dic dictionary to pyCharm settings

# TODO Check warning messages all over the application

# TODO Handle traffic limitation and excessive unsuccessful browser validation attempts

# TODO Open/close for each word in root/word display (on screen only)

# TODO dictionary text (BDB, Gesenius, ...) for Bible words

# TODO Arab <---> Hebrew roots correspondence

# TODO Arab search without vowels (and for Hebrew as well ...)

# ------------------------- Response building class --------------------------------------------------------------------
class Se3ResponseFactory:
    @classmethod
    def buildNew(cls, p_app, p_requestHandler, p_context):
        l_context = p_requestHandler.getContext()

        # single verse
        if l_context['K'] == 'V':
            return Se3_SingleVerse(p_app, p_requestHandler, p_context)
        # passage
        elif l_context['K'] == 'P':
            return Se3_Passage(p_app, p_requestHandler, p_context)
        # word (lexicon)
        elif l_context['K'][0] == 'W':
            return Se3_Word(p_app, p_requestHandler, p_context)
        # root
        elif l_context['K'][0] == 'R':
            return Se3_Root(p_app, p_requestHandler, p_context)
        # search
        elif l_context['K'][0] == 'S':
            return Se3_Search(p_app, p_requestHandler, p_context)
        # table of contents
        elif l_context['K'][0] == 'T':
            return Se3_Toc(p_app, p_requestHandler, p_context)
        # Arabic Lexicon
        elif l_context['K'][0] == 'L':
            return Se3_Lexicon(p_app, p_requestHandler, p_context)
        else:
            return '<p>No Response (You should not be seeing this!)</p>'

class Se3AppCore(EcAppCore):
    # --------------------- App Init -----------------------------------------------------------------------------------
    def __init__(self, p_templatePath):
        # init connection pool
        super().__init__(p_templatePath)

        self.m_homePageTemplatePath = p_templatePath

        # ---------------------- Logging ---------------------------------------------------------------------------------------
        self.m_loggerSE3 = logging.getLogger(EcAppParam.gcm_appName + '.se3_main')
        if EcAppParam.gcm_verboseModeOn:
            self.m_loggerSE3.setLevel(logging.INFO)
        if EcAppParam.gcm_debugModeOn:
            self.m_loggerSE3.setLevel(logging.DEBUG)

        # load the page template
        self.loadTemplates()

        # loads the versions lists (one for Bible, one for Quran)
        self.m_bibleVersionId = []  # l_versionId, l_language, l_default, l_labelShort, l_labelTiny for Bible versions
        self.m_quranVersionId = []  # l_versionId, l_language, l_default, l_labelShort, l_labelTiny for Quran versions
        self.init_versions()

        # loads the book/chapter dictionary
        self.m_bookChapter = {}
        self.init_book_chapter()

        # loads the book alias --> book ID dictionary
        self.m_bookAlias = {}
        self.init_book_alias()

    # ------------------ Templates--------------------------------------------------------------------------------------
    # there could be several templates but here there is only one (there are 2 others for the req. handler)
    def loadTemplates(self):
        # self.m_homePageTemplatePath
        # self.m_homePageTemplate

        try:
            with open(self.m_homePageTemplatePath, 'r') as l_fTemplate:
                self.m_homePageTemplate = l_fTemplate.read()
        except OSError as e:
            self.m_loggerSE3.critical(
                'Could not open template file [{0}]. Exception: [{1}]. Aborting.'.format(
                    self.m_homePageTemplatePath, str(e)))
            raise

        self.m_loggerSE3.info('Loaded template file [{0}].'.format(self.m_homePageTemplatePath))

    # --------------------- Version ID lists (Called at App Init) ------------------------------------------------------
    # self.m_bibleVersionId = []   # l_versionId, l_language, l_default, l_labelShort, l_labelTiny for Bible versions
    # self.m_quranVersionId = []   # l_versionId, l_language, l_default, l_labelShort, l_labelTiny for Quran versions

    # self.m_defaultBibleId = '1'  # Hexadecimal bit mask representation of the default Bible version ID
    # self.m_defaultQuranId = '1'  # same for Quran

    # these serve as default values for p_context['l'] and p_context['q'] respectively

    # helper function to avoid accessing global variables outside of their file
    def getVersionList(self, p_bibleQuran='B'):
        if p_bibleQuran == 'B':
            return self.m_bibleVersionId
        else:
            return self.m_quranVersionId

    # loads the version vectors from the database (performed at app startup)
    def init_versions(self):
        l_connector = self.m_connectionPool.getConnection()

        try:
            # all versions except ground text
            l_query = """
                select
                    V.ID_VERSION
                    , V.FL_BIBLE_QURAN
                    , V.ID_LANGUAGE
                    , V.FL_DEFAULT
                    , V.ST_LABEL_SHORT
                    , V.ST_LABEL_TINY
                    , B.TX_VERSE_INSENSITIVE
                from TB_VERSION V left outer join (
                    select ID_VERSION, TX_VERSE_INSENSITIVE
                    from TB_VERSES
                    where ID_BOOK='Qur' and N_CHAPTER=1 and N_VERSE=1
                ) B on V.ID_VERSION = B.ID_VERSION
                where V.ID_VERSION <> '_gr'
                order by V.N_ORDER
                ;"""

            self.m_loggerSE3.debug('l_query: {0}'.format(l_query))

            l_cursor = l_connector.cursor(buffered=True)
            l_cursor.execute(l_query)

            # binary mask variables used to set the value of g_defaultBibleId and g_defaultQuranId
            # they are multiplied by 2 (i.e. set to next bit) each time a Bible (resp. Quran) verse is encountered
            l_maskBible = 1
            l_maskQuran = 1

            # cursor iteration
            for l_versionId, l_bq, l_language, l_default, l_labelShort, l_labelTiny, l_basmalat in l_cursor:
                if l_bq == 'B':
                    self.m_bibleVersionId.append((l_versionId, l_language, l_default, l_labelShort, l_labelTiny, ''))

                    if l_default == 'Y':
                        # the slice is necessary because the output of hex() starts with '0x'
                        self.m_defaultBibleId = hex(l_maskBible)[2:].upper()

                    l_maskBible *= 2
                else:
                    self.m_quranVersionId.append((l_versionId, l_language, l_default, l_labelShort, l_labelTiny, l_basmalat))

                    if l_default == 'Y':
                        # the slice is necessary because the output of hex() starts with '0x'
                        self.m_defaultQuranId = hex(l_maskQuran)[2:].upper()

                    l_maskQuran *= 2

            l_cursor.close()

            self.m_loggerSE3.debug('g_bibleVersionId: {0}'.format(self.m_bibleVersionId))
            self.m_loggerSE3.debug('g_quranVersionId: {0}'.format(self.m_quranVersionId))

            self.m_connectionPool.releaseConnection(l_connector)

            self.m_loggerSE3.info('g_bibleVersionId loaded. Size: {0}'.format(len(self.m_bibleVersionId)))
            self.m_loggerSE3.info('g_quranVersionId loaded. Size: {0}'.format(len(self.m_quranVersionId)))
        except mysql.connector.Error as l_exception:
            self.m_loggerSE3.critical('Cannot load versions. Exception [{0}]. Aborting.'.format(l_exception))
            raise

    # ------------------------- Book/Chapter data (Called at App Init) -------------------------------------------------
    # self.m_bookChapter = {}

    # g_bookChapter['id'] = [(l_bibleQuran, l_idGroup0, l_idGroup1, l_bookPrev, l_bookNext), v1, v2, ... ,vn]
    #                        ^ first item in the list = tuple containing                     |<----------->|
    #                          various info about the chapter                                 see below
    #
    # v1, v2, ... ,vn = verse count for each chapter of the book (n = number of chapters for this book)
    #
    # Therefore: Verse count for a given chapter = g_bookChapter['id'][chapter number]
    #            Chapter count for the book = len(g_bookChapter['id']) - 1

    def chapterCount(self, p_bookId):
        return len(self.m_bookChapter[p_bookId]) - 1

    def getBookAttributes(self, p_bookId):
        return self.m_bookChapter[p_bookId][0]

    def getChapterVerseCount(self, p_bookId, p_chapter):
        return self.m_bookChapter[p_bookId][p_chapter]

    def init_book_chapter(self):
        l_connector = self.m_connectionPool.getConnection()

        try:
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
                self.m_bookChapter[l_bookId] = \
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
            g_loggerUtilities.debug('Cursor Created')
            l_cursor.execute(l_query)
            g_loggerUtilities.debug('Cursor Executed')

            # loads the chapter verse count terms of each g_bookChapter['id'] (from position 1 in the list onwards)
            for l_bookId, l_verseCount in l_cursor:
                self.m_bookChapter[l_bookId].append(l_verseCount)

            g_loggerUtilities.debug('g_bookChapter: {0}'.format(self.m_bookChapter))

            l_cursor.close()
            g_loggerUtilities.debug('Cursor Closed')

            self.m_connectionPool.releaseConnection(l_connector)
            g_loggerUtilities.debug('Connector released')

            g_loggerUtilities.info('g_bookChapter loaded. Size: {0}'.format(len(self.m_bookChapter)))
        except mysql.connector.Error as l_exception:
            g_loggerUtilities.critical(
                'Cannot load Books/Chapters. Mysql Exception [{0}]. Aborting.'.format(l_exception))
            raise
        except Exception as l_exception:
            g_loggerUtilities.critical(
                'Cannot load Books/Chapters. General Exception [{0}]. Aborting.'.format(l_exception))
            raise

    # ------------------------- Book Aliases table (Called at App Init) ------------------------------------------------
    # self.m_bookAlias = {}  # Dictionary giving the correct book ID from one of its allowed aliases
    # (rm, rom, ... --> Rom)

    def init_book_alias(self):
        l_connector = self.m_connectionPool.getConnection()

        try:
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
                self.m_bookAlias[l_bookAlias] = l_bookId

            l_cursor.close()
            self.m_connectionPool.releaseConnection(l_connector)

            g_loggerUtilities.info('g_bookAlias loaded. Size: {0}'.format(len(self.m_bookAlias)))
        except mysql.connector.Error as l_exception:
            g_loggerUtilities.critical('Cannot load book aliases. Exception [{0}]. Aborting.'.format(l_exception))
            raise

    # ------------------------- Version vector--------------------------------------------------------------------------
    # creates a string of the form "id1", "id2", ..., "idn" where the ids correspond to the selected versions
    # indicated by p_context['l'] (Bible) or p_context['q'] (Quran) depending on the value of p_context['b'] (book)
    # used to fill in the IN clauses of the SQL requests which filter versions

    def get_version_vector(self, p_context, p_forceAll=False):
        # Get the correct book name (assumes p_context['b'] belongs to g_bookAlias keys --> must have
        # been checked before)
        l_pcBookId = self.m_bookAlias[p_context['b'].lower().strip()]

        if p_forceAll:
            if l_pcBookId == 'Qur':
                l_versionList = self.m_quranVersionId
            else:
                l_versionList = self.m_bibleVersionId

            # the version Id is the first element (0th) of the tuple for each version
            l_vector = '"' + '", "'.join([v[0] for v in l_versionList]) + '"'
        else:
            l_vector = '"' + '", "'.join([v[0] for v in self.get_version_list(p_context)]) + '"'

        g_loggerUtilities.debug('l_vector: {0}'.format(l_vector))

        return l_vector

    # ------------------------- Version dictionary ---------------------------------------------------------------------
    # Same as above but the return value is a list of tuples instead of a string
    # Each tuple is of the form (l_versionId, l_language, l_default, l_labelShort, l_labelTiny, l_basmalat)
    #
    # p_context['q'] and p_context['l'] are hexadecimal bit vector representations of the selected versions
    # (resp. Quran and Bible). E.g. p_context['q'] = 1B = 11011 --> versions 1, 2, 4 and 5 are selected

    def get_version_list(self, p_context, p_QuranAndBible=False, p_forceBibleQuran=None):
        # if p_QuranAndBible = True --> get both versions from the Bible and Quran
        # otherwise decide based on p_context['b'] or p_forceBibleQuran if set

        # Get the correct book name (assumes p_context['b'] belongs to g_bookAlias keys --> must have been
        # checked before)
        l_pcBookId = self.m_bookAlias[p_context['b'].lower().strip()]

        if p_QuranAndBible:
            return self.get_vl_internal(self.m_quranVersionId, p_context['q']) + \
                   self.get_vl_internal(self.m_bibleVersionId, p_context['l'])
        else:
            # decision to return Bible or Quran version based on context (l_pcBookId) or p_forceBibleQuran if set
            l_bibleQuran = p_forceBibleQuran if p_forceBibleQuran is not None else l_pcBookId
            if l_bibleQuran[0:1] == 'Q':
                return self.get_vl_internal(self.m_quranVersionId, p_context['q'])
            else:
                return self.get_vl_internal(self.m_bibleVersionId, p_context['l'])

    # internal function doing the heavy lifting
    def get_vl_internal(self, p_versionList, p_versionWordStr):
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

    # ------------------------- Context preprocessing ------------------------------------------------------------------
    def preprocess_context(self, p_context, p_previousContext):
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
        if 'K' not in l_context.keys():
            if 'K' in p_previousContext.keys():
                l_context['K'] = p_previousContext['K']
            else:
                l_context['K'] = 'T'

        # Bible/Quran default versions -------------------------
        try:
            l_bibleVersionsInt = int(l_context['l'], 16)
        except ValueError:
            l_bibleVersionsInt = int(self.m_defaultBibleId, 16)
            l_context['l'] = self.m_defaultBibleId

        try:
            l_quranVersionsInt = int(l_context['q'], 16)
        except ValueError:
            l_quranVersionsInt = int(self.m_defaultQuranId, 16)
            l_context['q'] = self.m_defaultQuranId

        if l_bibleVersionsInt >= 2 ** len(self.m_bibleVersionId) or l_bibleVersionsInt == 0:
            l_context['l'] = self.m_defaultBibleId

        if l_quranVersionsInt >= 2 ** len(self.m_quranVersionId) or l_quranVersionsInt == 0:
            l_context['q'] = self.m_defaultQuranId

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
    def trap_references(self, p_context):
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
    def passage_control(self, p_context):
        l_book = p_context['b']
        l_chapter = p_context['c']
        l_verse1 = p_context['v']
        l_verse2 = p_context['w']

        # book must be in the alias table
        if l_book.lower().strip() not in self.m_bookAlias.keys():
            return EcAppCore.get_user_string(p_context, 'e_wrongBookPassage').format(
                l_book, l_chapter, l_verse1, l_verse2)
        else:
            # Get the correct book name (assumes p_context['b'] belongs to g_bookAlias keys as checked above)
            l_pcBookId = self.m_bookAlias[l_book.lower().strip()]

            # chapter must be a valid number
            try:
                l_intChapter = int(l_chapter)
            except ValueError:
                return EcAppCore.get_user_string(p_context, 'e_wrongChapterPassage').format(
                    l_book, l_chapter, l_verse1, l_verse2)

            # chapter must be in the right range based on the book table
            #if l_intChapter < 1 or l_intChapter > len(self.m_bookChapter[l_pcBookId]) - 1:
            if l_intChapter < 1 or l_intChapter > self.chapterCount(l_pcBookId):
                return EcAppCore.get_user_string(p_context, 'e_wrongChapterPassage').format(
                    l_book, l_chapter, l_verse1, l_verse2)
            else:
                # verse1 must be a valid number
                try:
                    l_intVerse1 = int(l_verse1)
                except ValueError:
                    return EcAppCore.get_user_string(p_context, 'e_wrongV1Passage').format(
                        l_book, l_chapter, l_verse1, l_verse2)

                l_intVerse2 = 0
                # verse2 must be a valid number except in the case where v1 = 1 and v2 = 'x' (indicating 'whole chapter)
                try:
                    l_intVerse2 = int(l_verse2)
                except ValueError:
                    if not (l_intVerse1 == 1 and l_verse2 == 'x'):
                        return EcAppCore.get_user_string(p_context, 'e_wrongV2Passage').format(
                            l_book, l_chapter, l_verse1, l_verse2)

                # v1 must be in the right range as determined based on the chapter and book
                #if l_intVerse1 < 1 or l_intVerse1 > self.m_bookChapter[l_pcBookId][l_intChapter]:
                if l_intVerse1 < 1 or l_intVerse1 > self.getChapterVerseCount(l_pcBookId, l_intChapter):
                    return EcAppCore.get_user_string(p_context, 'e_wrongV1Passage').format(
                        l_book, l_chapter, l_verse1, l_verse2)
                # v2 must be in the same range as v1 and also greater than v1
                elif l_verse2 != 'x' and \
                        (l_intVerse2 < 1 or l_intVerse2 > self.getChapterVerseCount(l_pcBookId, l_intChapter) or
                                 l_intVerse1 > l_intVerse2):
                    return EcAppCore.get_user_string(p_context, 'e_wrongV2Passage').format(
                        l_book, l_chapter, l_verse1, l_verse2)

        return ''

    # ensure correct values for the parameters needed by the verse command ('V')
    # called at the beginning of get_single_verse()
    def verse_control(self, p_context):
        l_book = p_context['b']
        l_chapter = p_context['c']
        l_verse = p_context['v']

        # book must be in the alias table
        if l_book.lower().strip() not in self.m_bookAlias.keys():
            return EcAppCore.get_user_string(p_context, 'e_wrongBookVerse').format(
                l_book, l_chapter, l_verse)
        else:
            # Get the correct book name (assumes p_context['b'] belongs to g_bookAlias keys as checked above)
            l_pcBookId = self.m_bookAlias[l_book.lower().strip()]

            # chapter must be a valid number
            try:
                l_intChapter = int(l_chapter)
            except ValueError:
                return EcAppCore.get_user_string(p_context, 'e_wrongChapterVerse').format(
                    l_book, l_chapter, l_verse)

            # chapter must be in the right range based on the book table
            #if l_intChapter < 1 or l_intChapter > len(self.m_bookChapter[l_pcBookId]) - 1:
            if l_intChapter < 1 or l_intChapter > self.chapterCount(l_pcBookId):
                return EcAppCore.get_user_string(p_context, 'e_wrongChapterVerse').format(
                    l_book, l_chapter, l_verse)
            else:
                # verse must be a valid number
                try:
                    l_intVerse = int(l_verse)
                except ValueError:
                    return EcAppCore.get_user_string(p_context, 'e_wrongVVerse').format(
                        l_book, l_chapter, l_verse)

                # verse must be in the right range as determined based on the chapter and book
                if l_intVerse < 1 or l_intVerse > self.getChapterVerseCount(l_pcBookId, l_intChapter):
                    return EcAppCore.get_user_string(p_context, 'e_wrongVVerse').format(
                        l_book, l_chapter, l_verse)

        return ''

    # ensure correct values for the parameters needed by the word command ('W')
    # called at the beginning of get_word()
    def word_control(self, p_context):
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
            return EcAppCore.get_user_string(p_context, 'e_wrongIdWord').format(
                l_book, l_chapter, l_verse, p_context['d'])

        l_wordId = p_context['d'].split('-')[0]
        l_interlinearId = p_context['d'].split('-')[1]
        l_idStrongs = p_context['d'].split('-')[2]

        # if both the word ID and the interlinear ID are '_' then there is no further test to perform
        # otherwise, all the tests below apply
        if not (l_wordId == '_' and l_interlinearId == '_'):
            # book must be in the alias table
            if l_book.lower().strip() not in self.m_bookAlias.keys():
                return EcAppCore.get_user_string(p_context, 'e_wrongBookWord').format(
                    l_book, l_chapter, l_verse, l_wordId, l_interlinearId, l_idStrongs)
            else:
                # Get the correct book name (assumes p_context['b'] belongs to g_bookAlias keys as checked above)
                l_pcBookId = self.m_bookAlias[l_book.lower().strip()]

                # chapter must be a valid number
                try:
                    l_intChapter = int(l_chapter)
                except ValueError:
                    return EcAppCore.get_user_string(p_context, 'e_wrongChapterWord').format(
                        l_book, l_chapter, l_verse, l_wordId, l_interlinearId, l_idStrongs)

                # chapter must be in the right range based on the book table
                #if l_intChapter < 1 or l_intChapter > len(self.m_bookChapter[l_pcBookId]) - 1:
                if l_intChapter < 1 or l_intChapter > self.chapterCount(l_pcBookId):
                    return EcAppCore.get_user_string(p_context, 'e_wrongChapterWord').format(
                        l_book, l_chapter, l_verse, l_wordId, l_interlinearId, l_idStrongs)
                else:
                    # verse must be a valid number
                    try:
                        l_intVerse = int(l_verse)
                    except ValueError:
                        return EcAppCore.get_user_string(p_context, 'e_wrongVWord').format(
                            l_book, l_chapter, l_verse, l_wordId, l_interlinearId, l_idStrongs)

                    # verse must be in the right range as determined based on the chapter and book
                    if l_intVerse < 1 or l_intVerse > self.getChapterVerseCount(l_pcBookId, l_intChapter):
                        return EcAppCore.get_user_string(p_context, 'e_wrongVWord').format(
                            l_book, l_chapter, l_verse, l_wordId, l_interlinearId, l_idStrongs)
                    else:
                        # word ID must be a valid number
                        try:
                            l_intWord = int(l_wordId)
                        except ValueError:
                            return EcAppCore.get_user_string(p_context, 'e_wrongWordWord').format(
                                l_book, l_chapter, l_verse, l_wordId, l_interlinearId, l_idStrongs)

                        # word number must be in a "reasonable" range
                        if l_intWord < 0 or l_intWord > 500:
                            return EcAppCore.get_user_string(p_context, 'e_wrongWordWord').format(
                                l_book, l_chapter, l_verse, l_wordId, l_interlinearId, l_idStrongs)

        return ''

    # ensure correct values for the parameters needed by the root command ('R')
    # called at the beginning of get_root()
    def root_control(self, p_context):
        l_rootString = p_context['d']

        # the word ID parameter must be a sequence of items separated by '|'. Each item is either
        # 1) a strongs number: Z9999 with Z = A, H or G and 9999 a 4 digit number, or
        # 2) a "pure root" ID of the form X-ZZZ with ZZZ any trigram of capital letters
        # 3) an Arabic root which can be any sequence of non-space letters
        if re.search('(\S{3}|[HGA][0-9]{4}|X-[A-Z]{3})(\|(\S{3}|[HGA][0-9]{4}|X-[A-Z]{3}))*', l_rootString) is None:
            return EcAppCore.get_user_string(p_context, 'e_wrongRoot').format(l_rootString)

        return ''

    # ------------------------- Chapter names (en/fr) ----------------------------------------------------------------------
    # get the French and English full chapter name corresponding to context (p_context['b'] + p_context['c'])
    def get_chapter_names(self, p_context, p_dbConnection):
        # Get the correct book name (assumes p_context['b'] belongs to g_bookAlias keys --> must have been checked before)
        l_pcBookId = self.m_bookAlias[p_context['b'].lower().strip()]

        l_query = """
            select ST_NAME_EN, ST_NAME_FR
            from TB_CHAPTER
            where
                ID_BOOK = '{0}'
                and N_CHAPTER = {1}
            ;""".format(l_pcBookId, p_context['c'])

        g_loggerUtilities.debug('l_query: {0}'.format(l_query))
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

    # -------------------- Call Point from EcRequestHandler ------------------------------------------------------------
    #def getResponse(self, p_previousContext, p_context, p_dbConnectionPool, p_urlPath, p_noJSPath, p_terminalID):
    def getResponse(self, p_requestHandler):
        self.m_loggerSE3.info('Getting response from App Core')

    #    return self.se3_entryPoint(p_requestHandler)

    # ---------------------- Application entry point -------------------------------------------------------------------
    #def se3_entryPoint(self, p_requestHandler):
        self.m_loggerSE3.info('Entering SE3')

        # if debugging, reload template for each request
        if EcAppParam.gcm_debugModeOn:
            self.loadTemplates()

        l_previousContext = p_requestHandler.getPreviousContext()

        # default values, certain common controls, parameter expansion, ...
        l_context = self.preprocess_context(p_requestHandler.getContext(), l_previousContext)

        # passage/book/verse references given in search box --> transformed into respective P/V commands
        l_context = self.trap_references(l_context)

        # +++++++++++++++++ A) response creation +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        # gets the proper response depending on the command parameter (l_context['K'])
        # this is not yet the whole page but only the part which goes in the main content area
        l_builder = Se3ResponseFactory.buildNew(self, p_requestHandler, l_context)
        l_response, l_context, l_title = l_builder.buildResponse()

        # +++++++++++++++++ B) substitution values +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

        # ............. B.1) header elements ...........................................................................

        l_bibleVersionControl, l_quranVersionControl, l_paramControl, l_statusDisplay = \
            self.build_header_controls(l_context)

        # ............. B.2) dimensions ................................................................................

        l_dimensions = self.get_dimensions()

        # ............. B.3) other elements ............................................................................
        # determines the values of all the §{xx} variables for the template substitution

        # dimensions table + context / previous context tables are displayed only in debug mode
        l_hiddenFieldsStyle, l_hiddenFieldsType, l_dimensionsTable, l_oldContextTable, l_newContextTable = \
            self.debugTables(l_dimensions, l_previousContext, l_context)

        # create appropriate template substitution key/values for each element of the context
        l_inputValues = {}
        for l_key, l_value in l_context.items():
            l_inputValues['inputValue_' + l_key] = l_value

        # NB : the value of t and u is 'checked' or '' and §{inputValue_t} / §{inputValue_u} are used
        # at the end of each checkbox input tag to indicate if it is checked or not. For example :

        # <input type="checkbox" id="NavControl_wholeWords" name="t" value="checked" §{inputValue_t}>

        # So this also sets the current value for t and u

        self.m_loggerSE3.debug('l_inputValues: {0}'.format(l_inputValues))

        # merge l_dimensions and l_inputValues
        l_substituteVar = l_dimensions
        l_substituteVar.update(l_inputValues)

        # add various labels all over the control section of the page, including comb box values
        l_substituteVar.update(self.get_labels(l_context))

        self.m_loggerSE3.debug('l_substituteVar: {0}'.format(l_substituteVar))

        # +++++++++++++++++ C) final substitution ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        l_urlPath, l_noJSPath = p_requestHandler.getPaths()
        l_terminalID = p_requestHandler.getTerminalID()
        l_pageTemplate = EcTemplate(self.m_homePageTemplate)
        l_response = l_pageTemplate.substitute(
            l_substituteVar,
            WindowTitle=l_title,
            UrlPath=l_urlPath,
            NoJSPath=l_noJSPath,
            FooterText='{0} v. {1}<br/>Terminal ID: {2}'.format(
               EcAppParam.gcm_appTitle, EcAppParam.gcm_appVersion, l_terminalID),
            HiddenFieldsStyle=l_hiddenFieldsStyle,
            HiddenFieldsType=l_hiddenFieldsType,
            StatusLine=l_statusDisplay,
            Parameters=l_paramControl,
            BibleVersions=l_bibleVersionControl,
            QuranVersions=l_quranVersionControl,
            Response=l_response,
            OldContextTable=l_oldContextTable,
            NewContextTable=l_newContextTable,
            DimensionsTable=l_dimensionsTable
        )

        self.m_loggerSE3.info('SE3 returning')
        return l_response, l_context

    # dimensions table + context / previous context tables are displayed only in debug mode
    def debugTables(self, p_dimensions, p_previousContext, p_context):
        l_dimensionsTable = ''
        l_oldContextTable = ''
        l_newContextTable = ''

        if EcAppParam.gcm_debugModeOn:
            l_hiddenFieldsType = 'text'
            l_hiddenFieldsStyle = ''

            l_dimensionsTable = '<p>Dimensions:</p><table style="border: 1px solid black;">'
            for l_key in p_dimensions.keys():
                l_dimensionsTable += '<tr><td>{0}</td><td>{1}</td></tr>'.format(l_key, p_dimensions[l_key])
            l_dimensionsTable += '</table>\n'

            l_oldContextTable = '<p>Old Context:</p><table style="border: 1px solid black;">'
            for l_key, l_value in p_previousContext.items():
                l_oldContextTable += '<tr><td>{0}</td><td>{1}</td></tr>'.format(l_key, l_value)
            l_oldContextTable += '</table>\n'

            l_newContextTable = '<p>Context:</p><table style="border: 1px solid black;">'
            for l_key, l_value in p_context.items():
                l_newContextTable += '<tr><td>{0}</td><td>{1}</td></tr>'.format(l_key, l_value)
            l_newContextTable += '</table>\n'
        else:
            l_hiddenFieldsType = 'hidden'
            l_hiddenFieldsStyle = 'display: none;'

        return l_hiddenFieldsStyle, l_hiddenFieldsType, l_dimensionsTable, l_oldContextTable, l_newContextTable

    # various labels all over the control section of the page, including comb box values
    def get_labels(self, p_context):
        l_substituteVar = dict()

        # Search form labels and current values
        l_substituteVar['label_search'] = self.get_user_string(p_context, 'm_labelSearch')
        l_substituteVar['label_wholeWords'] = self.get_user_string(p_context, 'm_labelWholeWords')
        l_substituteVar['label_caseSensitive'] = self.get_user_string(p_context, 'm_labelCaseSensitive')
        l_substituteVar['label_exclude'] = self.get_user_string(p_context, 'm_labelExclude')
        l_substituteVar['label_searchScope'] = self.get_user_string(p_context, 'm_labelSearchScope')

        # Search mode value labels
        l_substituteVar['label_searchMode'] = self.get_user_string(p_context, 'm_labelSearchMode')
        l_substituteVar['label_searchMode0'] = self.get_user_string(p_context, 'm_labelSearchMode0')
        l_substituteVar['label_searchMode1'] = self.get_user_string(p_context, 'm_labelSearchMode1')
        l_substituteVar['label_searchMode2'] = self.get_user_string(p_context, 'm_labelSearchMode2')

        # Search mode current value
        l_substituteVar['inputValue_e0'] = ''
        l_substituteVar['inputValue_e1'] = ''
        l_substituteVar['inputValue_e2'] = ''
        l_substituteVar['inputValue_e' + p_context['e']] = 'selected'

        # Quran scope value labels
        l_substituteVar['label_searchScopeQ'] = self.get_user_string(p_context, 'm_labelSearchScopeQ')
        l_substituteVar['label_searchScopeQ0'] = self.get_user_string(p_context, 'm_labelSearchScopeQ0')
        l_substituteVar['label_searchScopeQ1'] = self.get_user_string(p_context, 'm_labelSearchScopeQ1')

        # Quran scope current value
        l_substituteVar['inputValue_h0'] = ''
        l_substituteVar['inputValue_h1'] = ''
        l_substituteVar['inputValue_h' + p_context['h']] = 'selected'

        # NT scope value labels
        l_substituteVar['label_searchScopeNT'] = self.get_user_string(p_context, 'm_labelSearchScopeNT')
        l_substituteVar['label_searchScopeNT0'] = self.get_user_string(p_context, 'm_labelSearchScopeNT0')
        l_substituteVar['label_searchScopeNT1'] = self.get_user_string(p_context, 'm_labelSearchScopeNT1')
        l_substituteVar['label_searchScopeNT2'] = self.get_user_string(p_context, 'm_labelSearchScopeNT2')
        l_substituteVar['label_searchScopeNT3'] = self.get_user_string(p_context, 'm_labelSearchScopeNT3')
        l_substituteVar['label_searchScopeNT4'] = self.get_user_string(p_context, 'm_labelSearchScopeNT4')

        # NT scope current value
        l_substituteVar['inputValue_i0'] = ''
        l_substituteVar['inputValue_i1'] = ''
        l_substituteVar['inputValue_i2'] = ''
        l_substituteVar['inputValue_i3'] = ''
        l_substituteVar['inputValue_i4'] = ''
        l_substituteVar['inputValue_i' + p_context['i']] = 'selected'

        # OT scope value labels
        l_substituteVar['label_searchScopeOT'] = self.get_user_string(p_context, 'm_labelSearchScopeOT')
        l_substituteVar['label_searchScopeOT0'] = self.get_user_string(p_context, 'm_labelSearchScopeOT0')
        l_substituteVar['label_searchScopeOT1'] = self.get_user_string(p_context, 'm_labelSearchScopeOT1')
        l_substituteVar['label_searchScopeOT2'] = self.get_user_string(p_context, 'm_labelSearchScopeOT2')
        l_substituteVar['label_searchScopeOT3'] = self.get_user_string(p_context, 'm_labelSearchScopeOT3')
        l_substituteVar['label_searchScopeOT4'] = self.get_user_string(p_context, 'm_labelSearchScopeOT4')
        l_substituteVar['label_searchScopeOT5'] = self.get_user_string(p_context, 'm_labelSearchScopeOT5')

        # OT scope current value
        l_substituteVar['inputValue_j0'] = ''
        l_substituteVar['inputValue_j1'] = ''
        l_substituteVar['inputValue_j2'] = ''
        l_substituteVar['inputValue_j3'] = ''
        l_substituteVar['inputValue_j4'] = ''
        l_substituteVar['inputValue_j5'] = ''
        l_substituteVar['inputValue_j' + p_context['j']] = 'selected'

        # TOC labels
        l_substituteVar['toc_allScripture'] = self.get_user_string(p_context, 'm_tocAllScripture')
        l_substituteVar['toc_Quran'] = self.get_user_string(p_context, 'm_quran')
        l_substituteVar['toc_QuranRev'] = self.get_user_string(p_context, 'm_tocQuranRev')
        l_substituteVar['toc_NT'] = self.get_user_string(p_context, 'm_labelSearchScopeNT')
        l_substituteVar['toc_OT'] = self.get_user_string(p_context, 'm_labelSearchScopeOT')
        l_substituteVar['toc_toc'] = self.get_user_string(p_context, 'm_tocToc')

        # Lexicon labels
        l_substituteVar['lex_Arabic'] = self.get_user_string(p_context, 'm_lexArabic')
        l_substituteVar['lex_Greek'] = self.get_user_string(p_context, 'm_lexGreek')
        l_substituteVar['lex_Hebrew'] = self.get_user_string(p_context, 'm_lexHebrew')
        l_substituteVar['lex_lex'] = self.get_user_string(p_context, 'm_lexLex')

        # Apply button label
        l_substituteVar['ApplyLabel'] = self.get_user_string(p_context, 'm_ApplyLabel')

        # Left panel section collapse buttons in open and closed positions
        l_substituteVar['CollapsarShow'] = self.get_user_string(p_context, 'm_CollapsarShow')
        l_substituteVar['CollapsarHide'] = self.get_user_string(p_context, 'm_CollapsarHide')

        return l_substituteVar

    # Most of the CSS code is located in basic.css and print.css
    # However, some CSS definitions are located within the index.html template file
    # They are those which include dimension items which are set at template substitution time based on the
    # variables below.

    # Some HTML tags in the template need to have CSS coming both from basic.css/print.css (for different behavior
    # on screen and in print) and from the template (for dimensions). In these cases, the tags have both an id (located
    # in basic.css/print.css, for precedence sake) and a class located in the template.
    # When the id is of the form Xxx, the class is of the form XxxProxy
    # The tags involved are:
    # <header>
    # <nav>
    # <div id="Content">
    # <div id="RestOfPage">
    def get_dimensions(self):
        # all values in em
        l_dimensions = dict()

        # width of the left panel (search controls, TOC, ...)
        l_dimensions['NavWidth'] = 12
        # width of the show/hide control for the left panel
        l_dimensions['NavShowHideWidth'] = .8

        # padding at the top of the left panel
        l_dimensions['NavTopPadding'] = 1.2
        # padding on both sides of the left panel
        l_dimensions['NavLeftPadding'] = 1
        l_dimensions['NavRightPadding'] = 1

        # margin for all components inside the upper (smaller part) of the header
        l_dimensions['HeaderMargin'] = .5
        # logo width calculation
        l_dimensions['LogoWidth'] = l_dimensions['NavWidth'] - l_dimensions['NavLeftPadding']

        # header height in its closed form
        l_dimensions['HeaderHeight'] = 2
        # header height in its opened form
        l_dimensions['HeaderHeightBig'] = 15.2
        # height calculation for the open/close header control
        l_dimensions['BigSmallHeight'] = l_dimensions['HeaderHeight'] - 2*l_dimensions['HeaderMargin']
        # margin on the top of the open/close header control when the header is open
        l_dimensions['MarginBigSmallBig'] = \
            l_dimensions['HeaderHeightBig'] - l_dimensions['HeaderMargin'] - l_dimensions['BigSmallHeight']

        # left panel contents width calculation
        l_dimensions['NavContentWidth'] = l_dimensions['NavWidth'] - l_dimensions['NavShowHideWidth']
        # search form width calculation
        l_dimensions['NavFormWidth'] = l_dimensions['NavWidth'] - (
            l_dimensions['NavRightPadding'] + l_dimensions['NavLeftPadding'] + l_dimensions['NavShowHideWidth'])

        return l_dimensions

    def build_header_controls(self, p_context):
        # number of version selection checkboxes per column
        l_segmentLength = 10
        # Max number of versions to display in the status display
        l_selectedLimit = 4

        # Bible version list for the status display (beginning)
        l_statusDisplay = '<b>{0}</b>: '.format(self.get_user_string(p_context, 'm_bible'))

        # Bible versions selection checkboxes (beginning)
        l_bibleVersionControl = '<div class="VersionSegment">' + \
                                '<div class="VersionSelector"><b>{0}</b>:</div>'.format(
                                    self.get_user_string(p_context, 'm_bibleVersions'))

        # produce both the status display Bible version list and the Bible version selection checkbox block
        l_segmentCount = 1
        l_verMask = 1
        l_selectedCount = 0
        l_selectedList = [v[0] for v in self.get_version_list(p_context, False, 'B')]
        for l_versionId, l_language, l_default, l_labelShort, l_labelTiny, l_basmalat in self.getVersionList('B'):
            # Bible selection checkboxes
            # Each checkbox row is enclosed in a <div class="VersionSelector"> together with its label
            # The checkbox format is:
            #
            # <input type="checkbox" value="" class="ToggleVersion" name="" ver_mask="xx" bible_quran="B" yy>
            #
            # xx = hexadecimal bit mask indicating the version
            # yy = 'checked' if version selected or nothing otherwise
            l_bibleVersionControl += ('<div class="VersionSelector">' +
                                      '<input type="checkbox" value="" ' +
                                      'class="ToggleVersion ToggleVersionBible" name="" ver_mask="{2}" ' +
                                      'bible_quran="B" {1}>&nbsp{0}</div>\n').format(
                l_labelShort,
                'checked' if l_versionId in l_selectedList else '',
                l_verMask
            )

            # status display Bible version list
            if l_versionId in l_selectedList and l_selectedCount < l_selectedLimit:
                l_statusDisplay += l_labelTiny + ', '
                l_selectedCount += 1

            l_segmentCount += 1
            l_verMask *= 2
            # column break if column height reached
            if l_segmentCount % l_segmentLength == 0:
                l_segmentCount = 0
                l_bibleVersionControl += '</div><div class="VersionSegment">'

        l_statusDisplay = re.sub(',\s$', '', l_statusDisplay)
        # adding ... at the end of the status display if there are more Bible versions than the limit
        if len(l_selectedList) > l_selectedLimit:
            l_statusDisplay += ', ... '
        else:
            l_statusDisplay += ' '

        l_bibleVersionControl += ' <input type="button" id="UnselectAllBible" value="{0}"></div>\n'.format(
            self.get_user_string(p_context, 'm_unselectAll'))
        l_bibleVersionControl = re.sub('<div class="VersionSegment"></div>$', '', l_bibleVersionControl)

        # Quran versions selection checkboxes (beginning)
        l_quranVersionControl = '<div class="VersionSegment">' + \
                                '<div class="VersionSelector"><b>{0}</b>:</div>'.format(
                                    self.get_user_string(p_context, 'm_quranVersions'))

        # Quran version list for the status display (beginning)
        l_statusDisplay += '<b>{0}</b>: '.format(self.get_user_string(p_context, 'm_quran'))

        # produce both the status display Quran version list and the Quran version selection checkbox block
        l_segmentCount = 1
        l_verMask = 1
        l_selectedCount = 0
        l_selectedList = [v[0] for v in self.get_version_list(p_context, False, 'Q')]
        for l_versionId, l_language, l_default, l_labelShort, l_labelTiny, l_basmalat in self.getVersionList('Q'):
            # Quran selection checkboxes
            # Each checkbox row is enclosed in a <div class="VersionSelector"> together with its label
            # The checkbox format is:
            #
            # <input type="checkbox" value="" class="ToggleVersion" name="" ver_mask="xx" bible_quran="B" yy>
            #
            # xx = hexadecimal bit mask indicating the version
            # yy = 'checked' if version selected or nothing otherwise
            l_quranVersionControl += ('<div class="VersionSelector"><input type="checkbox" value="" ' +
                                      'class="ToggleVersion ToggleVersionQuran" name="" ver_mask="{2}" ' +
                                      'bible_quran="Q" {1}>&nbsp{0}</div>\n').format(
                l_labelShort,
                'checked' if l_versionId in l_selectedList else '',
                l_verMask
            )

            # status display Quran version list
            if l_versionId in l_selectedList and l_selectedCount < l_selectedLimit:
                l_statusDisplay += l_labelTiny + ', '
                l_selectedCount += 1

            l_segmentCount += 1
            l_verMask *= 2
            # column break if column height reached
            if l_segmentCount % l_segmentLength == 0:
                l_segmentCount = 0
                l_quranVersionControl += '</div><div class="VersionSegment">'

        l_statusDisplay = re.sub(',\s$', '', l_statusDisplay)
        # adding ... at the end of the status display if there are more Quran versions than the limit
        if len(l_selectedList) > l_selectedLimit:
            l_statusDisplay += ', ... '

        l_quranVersionControl += ' <input type="button" id="UnselectAllQuran" value="{0}"></div>\n'.format(
            self.get_user_string(p_context, 'm_unselectAll'))
        l_quranVersionControl = re.sub('<div class="VersionSegment"></div>$', '', l_quranVersionControl)

        # parameter checkboxes (same formatting as version checkboxes)
        l_paramControl = '<div class="VersionSegment">' +\
                         '<div class="VersionSelector"><b>{0}</b>:</div>'.format(
                             self.get_user_string(p_context, 'm_paramControl'))

        # list of tuples used to feed the loop below. Contains all the necessary elements for each parameter checkbox
        l_tmpList = [
            # the substitution is because some labels have '·' instead of ' ' in order to separate words
            (self.get_user_string(p_context, 'sv_AllVersions'),
             p_context['a'],
             Se3AppParam.gcm_svAllVersions),
            (self.get_user_string(p_context, 'm_DisplayLxx'),
             p_context['x'],
             Se3AppParam.gcm_svDisplayLxx),
            (self.get_user_string(p_context, 'm_DisplayNasb'),
             p_context['n'],
             Se3AppParam.gcm_svDisplayNasb),
            (self.get_user_string(p_context, 'm_DisplayKJV'),
             p_context['k'],
             Se3AppParam.gcm_svDisplayKjv),
            (self.get_user_string(p_context, 'p_displayGround'),
             p_context['g'],
             Se3AppParam.gcm_pDisplayGround),
            (self.get_user_string(p_context, 'p_parallelVersions'),
             p_context['r'],
             Se3AppParam.gcm_pParallel)
        ]

        for l_label, l_condition, l_mask in l_tmpList:
            l_paramControl += ('<div class="VersionSelector"><input type="checkbox"  value="" ' +
                               'class="ToggleParameter" name="" param_mask="{2}" ' +
                               '{1}>&nbsp{0}</div>\n').format(
                # the substitution is because some labels have '·' instead of ' ' in order to separate words
                re.sub('·', ' ', l_label),
                'checked' if l_condition else '',
                l_mask
            )

        l_paramControl += '</div>'

        return l_bibleVersionControl, l_quranVersionControl, l_paramControl, l_statusDisplay


