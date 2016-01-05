# -*- coding: utf-8 -*-

import sys
import re
import logging

from ec_app_params import *
import se3_single_verse
import se3_passage
import se3_word
import se3_root
import se3_search
import se3_utilities

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
# y
# z - UI language                                   All

# NOTE - Adding french spell-check dictionary to pyCharm:
# sudo apt-get install aspell-fr
# aspell --lang fr_FR dump master | aspell --lang fr expand | tr ' ' '\n' > french.dic
# french.dic must be in a dir by itself
# then add the french.dic dictionary to pyCharm settings

# TODO Verse ref display in single verse (box on the upper-left quadrant like in QuranSE II)

# TODO title display (for browser title bar) in all modules

# TODO why does bold not appear in search results when printing ?

# TODO blocking request from non-compliant browsers and maybe robots (at least some of them)

# TODO Testing for JS availability and cookies

# TODO Open/close for each root in root display (on screen only)

# TODO dictionary text (BDB, Gesenius, ...) for Bible words

# ---------------------- Logging ---------------------------------------------------------------------------------------
g_loggerSE3 = logging.getLogger(g_appName + '.se3_main')
if g_verboseModeOn:
    g_loggerSE3.setLevel(logging.INFO)
if g_debugModeOn:
    g_loggerSE3.setLevel(logging.DEBUG)

# ---------------------- Templates--------------------------------------------------------------------------------------
# there could be several templates but here there is only one
g_homePageTemplatePath = ''
g_homePageTemplate = ''


def loadTemplates():
    global g_homePageTemplatePath
    global g_homePageTemplate

    try:
        with open(g_homePageTemplatePath, 'r') as l_fTemplate:
            g_homePageTemplate = l_fTemplate.read()
    except OSError as e:
        g_loggerSE3.critical('Could not open template file [{0}]. Aborting.'.format(g_homePageTemplatePath))
        g_loggerSE3.critical('Exception: {0}'.format(str(e)))
        sys.exit()

    g_loggerSE3.info('Loaded template file [{0}].'.format(g_homePageTemplatePath))


# ---------------------- Application Init point ------------------------------------------------------------------------
def init(p_templatePath):
    global g_homePageTemplatePath

    g_homePageTemplatePath = p_templatePath
    # load the page template
    loadTemplates()
    # loads the versions lists (one for Bible, one for Quran)
    se3_utilities.init_versions()
    # loads the book/chapter dictionary
    se3_utilities.init_book_chapter()
    # loads the book alias --> book ID dictionary
    se3_utilities.init_book_alias()


# ---------------------- Application entry point -------------------------------------------------------------------
def se3_entryPoint(p_previousContext, p_context, p_dbConnectionPool):
    global g_homePageTemplatePath
    global g_homePageTemplate

    g_loggerSE3.info('Entering SE3')

    # if debugging, reload template for each request
    if g_debugModeOn:
        loadTemplates()

    # default values, certain common controls, parameter expansion, ...
    l_context = se3_utilities.preprocess_context(p_context, p_previousContext)

    # passage/book/verse references given in search box --> transformed into respective P/V commands
    l_context = se3_utilities.trap_references(l_context)

    # +++++++++++++++++ A) response creation +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # gets the proper response depending on the command parameter (l_context['K'])
    # this is not yet the whole page but only the part which goes in the main content area

    # sigle verse
    if l_context['K'] == 'V':
        l_response, l_context = se3_single_verse.get_single_verse(p_previousContext, l_context, p_dbConnectionPool)
    # passage
    elif l_context['K'] == 'P':
        l_response, l_context = se3_passage.get_passage(p_previousContext, l_context, p_dbConnectionPool)
    # word (lexicon)
    elif l_context['K'][0] == 'W':
        l_response, l_context = se3_word.get_word(p_previousContext, l_context, p_dbConnectionPool)
    # root
    elif l_context['K'][0] == 'R':
        l_response, l_context = se3_root.get_root(p_previousContext, l_context, p_dbConnectionPool)
    # search
    elif l_context['K'][0] == 'S':
        l_response, l_context = se3_search.get_search(p_previousContext, l_context, p_dbConnectionPool)
    # table of contents
    elif l_context['K'][0] == 'T':
        l_response, l_context = get_toc(p_previousContext, l_context, p_dbConnectionPool)
    else:
        l_response = '<p>No Response (You should not be seeing this!)</p>'

    # +++++++++++++++++ B) substitution values +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

    # ............. B.1) header elements ...............................................................................

    l_bibleVersionControl, l_quranVersionControl, l_paramControl, l_statusDisplay = \
        internal_get_header_controls(l_context)

    # ............. B.2) dimensions ....................................................................................

    l_dimensions = internal_get_dimensions()

    # ............. B.3) other elements ................................................................................
    # determines the values of all the §{xx} variables for the template substitution

    # dimensions table + context / previous context tables are displayed only in debug mode
    l_dimensionsTable = ''
    l_oldContextTable = ''
    l_newContextTable = ''

    if g_debugModeOn:
        l_hiddenFieldsType = 'text'
        l_hiddenFieldsStyle = ''

        l_dimensionsTable = '<p>Dimensions:</p><table style="border: 1px solid black;">'
        for l_key in l_dimensions.keys():
            l_dimensionsTable += '<tr><td>{0}</td><td>{1}</td></tr>'.format(l_key, l_dimensions[l_key])
        l_dimensionsTable += '</table>\n'

        l_oldContextTable = '<p>Old Context:</p><table style="border: 1px solid black;">'
        for l_key, l_value in p_previousContext.items():
            l_oldContextTable += '<tr><td>{0}</td><td>{1}</td></tr>'.format(l_key, l_value)
        l_oldContextTable += '</table>\n'

        l_newContextTable = '<p>Context:</p><table style="border: 1px solid black;">'
        for l_key, l_value in l_context.items():
            l_newContextTable += '<tr><td>{0}</td><td>{1}</td></tr>'.format(l_key, l_value)
        l_newContextTable += '</table>\n'
    else:
        l_hiddenFieldsType = 'hidden'
        l_hiddenFieldsStyle = 'display: none;'

    # create appropriate template substitution key/values for each element of the context
    l_inputValues = {}
    for l_key, l_value in l_context.items():
        l_inputValues['inputValue_' + l_key] = l_value

    # NB : the value of t and u is 'checked' or '' and §{inputValue_t} / §{inputValue_u} are used
    # at the end of each checkbox input tag to indicate if it is checked or not. For example :

    # <input type="checkbox" id="NavControl_wholeWords" name="t" value="checked" §{inputValue_t}>

    # So this also sets the current value for t and u

    g_loggerSE3.debug('l_inputValues: {0}'.format(l_inputValues))

    # merge l_dimensions and l_inputValues
    l_substituteVar = l_dimensions
    l_substituteVar.update(l_inputValues)

    l_substituteVar.update(internal_get_labels(l_context))

    g_loggerSE3.debug('l_substituteVar: {0}'.format(l_substituteVar))

    # +++++++++++++++++ C) final substitution ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    l_pageTemplate = se3_utilities.EcTemplate(g_homePageTemplate)
    l_response = l_pageTemplate.substitute(l_substituteVar,
                                           HiddenFieldsStyle=l_hiddenFieldsStyle,
                                           HiddenFieldsType=l_hiddenFieldsType,
                                           StatusLine=l_statusDisplay,
                                           Parameters=l_paramControl,
                                           BibleVersions=l_bibleVersionControl,
                                           QuranVersions=l_quranVersionControl,
                                           Response=l_response,
                                           OldContextTable=l_oldContextTable,
                                           NewContextTable=l_newContextTable,
                                           DimensionsTable=l_dimensionsTable)

    g_loggerSE3.info('SE3 returning')
    return l_response, l_context


def internal_get_labels(p_context):
    l_substituteVar = dict()

    # Search form labels and current values
    l_substituteVar['label_search'] = se3_utilities.get_user_string(p_context, 'm_labelSearch')
    l_substituteVar['label_wholeWords'] = se3_utilities.get_user_string(p_context, 'm_labelWholeWords')
    l_substituteVar['label_caseSensitive'] = se3_utilities.get_user_string(p_context, 'm_labelCaseSensitive')
    l_substituteVar['label_exclude'] = se3_utilities.get_user_string(p_context, 'm_labelExclude')
    l_substituteVar['label_searchScope'] = se3_utilities.get_user_string(p_context, 'm_labelSearchScope')

    # Search mode value labels
    l_substituteVar['label_searchMode'] = se3_utilities.get_user_string(p_context, 'm_labelSearchMode')
    l_substituteVar['label_searchMode0'] = se3_utilities.get_user_string(p_context, 'm_labelSearchMode0')
    l_substituteVar['label_searchMode1'] = se3_utilities.get_user_string(p_context, 'm_labelSearchMode1')
    l_substituteVar['label_searchMode2'] = se3_utilities.get_user_string(p_context, 'm_labelSearchMode2')

    # Search mode current value
    l_substituteVar['inputValue_e0'] = ''
    l_substituteVar['inputValue_e1'] = ''
    l_substituteVar['inputValue_e2'] = ''
    l_substituteVar['inputValue_e' + p_context['e']] = 'selected'

    # Quran scope value labels
    l_substituteVar['label_searchScopeQ'] = se3_utilities.get_user_string(p_context, 'm_labelSearchScopeQ')
    l_substituteVar['label_searchScopeQ0'] = se3_utilities.get_user_string(p_context, 'm_labelSearchScopeQ0')
    l_substituteVar['label_searchScopeQ1'] = se3_utilities.get_user_string(p_context, 'm_labelSearchScopeQ1')

    # Quran scope current value
    l_substituteVar['inputValue_h0'] = ''
    l_substituteVar['inputValue_h1'] = ''
    l_substituteVar['inputValue_h' + p_context['h']] = 'selected'

    # NT scope value labels
    l_substituteVar['label_searchScopeNT'] = se3_utilities.get_user_string(p_context, 'm_labelSearchScopeNT')
    l_substituteVar['label_searchScopeNT0'] = se3_utilities.get_user_string(p_context, 'm_labelSearchScopeNT0')
    l_substituteVar['label_searchScopeNT1'] = se3_utilities.get_user_string(p_context, 'm_labelSearchScopeNT1')
    l_substituteVar['label_searchScopeNT2'] = se3_utilities.get_user_string(p_context, 'm_labelSearchScopeNT2')
    l_substituteVar['label_searchScopeNT3'] = se3_utilities.get_user_string(p_context, 'm_labelSearchScopeNT3')
    l_substituteVar['label_searchScopeNT4'] = se3_utilities.get_user_string(p_context, 'm_labelSearchScopeNT4')

    # NT scope current value
    l_substituteVar['inputValue_i0'] = ''
    l_substituteVar['inputValue_i1'] = ''
    l_substituteVar['inputValue_i2'] = ''
    l_substituteVar['inputValue_i3'] = ''
    l_substituteVar['inputValue_i4'] = ''
    l_substituteVar['inputValue_i' + p_context['i']] = 'selected'

    # OT scope value labels
    l_substituteVar['label_searchScopeOT'] = se3_utilities.get_user_string(p_context, 'm_labelSearchScopeOT')
    l_substituteVar['label_searchScopeOT0'] = se3_utilities.get_user_string(p_context, 'm_labelSearchScopeOT0')
    l_substituteVar['label_searchScopeOT1'] = se3_utilities.get_user_string(p_context, 'm_labelSearchScopeOT1')
    l_substituteVar['label_searchScopeOT2'] = se3_utilities.get_user_string(p_context, 'm_labelSearchScopeOT2')
    l_substituteVar['label_searchScopeOT3'] = se3_utilities.get_user_string(p_context, 'm_labelSearchScopeOT3')
    l_substituteVar['label_searchScopeOT4'] = se3_utilities.get_user_string(p_context, 'm_labelSearchScopeOT4')
    l_substituteVar['label_searchScopeOT5'] = se3_utilities.get_user_string(p_context, 'm_labelSearchScopeOT5')

    # OT scope current value
    l_substituteVar['inputValue_j0'] = ''
    l_substituteVar['inputValue_j1'] = ''
    l_substituteVar['inputValue_j2'] = ''
    l_substituteVar['inputValue_j3'] = ''
    l_substituteVar['inputValue_j4'] = ''
    l_substituteVar['inputValue_j5'] = ''
    l_substituteVar['inputValue_j' + p_context['j']] = 'selected'

    # TOC labels
    l_substituteVar['toc_allScripture'] = se3_utilities.get_user_string(p_context, 'm_tocAllScripture')
    l_substituteVar['toc_Quran'] = se3_utilities.get_user_string(p_context, 'm_quran')
    l_substituteVar['toc_QuranRev'] = se3_utilities.get_user_string(p_context, 'm_tocQuranRev')
    l_substituteVar['toc_NT'] = se3_utilities.get_user_string(p_context, 'm_labelSearchScopeNT')
    l_substituteVar['toc_OT'] = se3_utilities.get_user_string(p_context, 'm_labelSearchScopeOT')
    l_substituteVar['toc_toc'] = se3_utilities.get_user_string(p_context, 'm_tocToc')

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
def internal_get_dimensions():
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


def internal_get_header_controls(p_context):
    # number of version selection checkboxes per column
    l_segmentLength = 9
    # Max number of versions to display in the status display
    l_selectedLimit = 4

    # Bible version list for the status display (beginning)
    l_statusDisplay = '<b>{0}</b>: '.format(se3_utilities.get_user_string(p_context, 'm_bible'))

    # Bible versions selection checkboxes (beginning)
    l_bibleVersionControl = '<div class="VersionSegment">' + \
                            '<div class="VersionSelector"><b>{0}</b>:</div>'.format(
                                se3_utilities.get_user_string(p_context, 'm_bibleVersions'))

    # produce both the status display Bible version list and the Bible version selection checkbox block
    l_segmentCount = 1
    l_verMask = 1
    l_selectedCount = 0
    l_selectedList = [v[0] for v in se3_utilities.get_version_list(p_context, False, 'B')]
    for l_versionId, l_language, l_default, l_labelShort, l_labelTiny in se3_utilities.getVersionList('B'):
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
                                  'class="ToggleVersion" name="" ver_mask="{2}" ' +
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

    l_bibleVersionControl += '</div>\n'
    l_bibleVersionControl = re.sub('<div class="VersionSegment"></div>$', '', l_bibleVersionControl)

    # Quran versions selection checkboxes (beginning)
    l_quranVersionControl = '<div class="VersionSegment">' + \
                            '<div class="VersionSelector"><b>{0}</b>:</div>'.format(
                                se3_utilities.get_user_string(p_context, 'm_quranVersions'))

    # Quran version list for the status display (beginning)
    l_statusDisplay += '<b>{0}</b>: '.format(se3_utilities.get_user_string(p_context, 'm_quran'))

    # produce both the status display Quran version list and the Quran version selection checkbox block
    l_segmentCount = 1
    l_verMask = 1
    l_selectedCount = 0
    l_selectedList = [v[0] for v in se3_utilities.get_version_list(p_context, False, 'Q')]
    for l_versionId, l_language, l_default, l_labelShort, l_labelTiny in se3_utilities.getVersionList('Q'):
        # Quran selection checkboxes
        # Each checkbox row is enclosed in a <div class="VersionSelector"> together with its label
        # The checkbox format is:
        #
        # <input type="checkbox" value="" class="ToggleVersion" name="" ver_mask="xx" bible_quran="B" yy>
        #
        # xx = hexadecimal bit mask indicating the version
        # yy = 'checked' if version selected or nothing otherwise
        l_quranVersionControl += ('<div class="VersionSelector"><input type="checkbox" value="" ' +
                                  'class="ToggleVersion" name="" ver_mask="{2}" ' +
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

    l_quranVersionControl += '</div>'
    l_quranVersionControl = re.sub('<div class="VersionSegment"></div>$', '', l_quranVersionControl)

    # parameter checkboxes (same formatting as version checkboxes)
    l_paramControl = '<div class="VersionSegment">' +\
                     '<div class="VersionSelector"><b>{0}</b>:</div>'.format(
                         se3_utilities.get_user_string(p_context, 'm_paramControl'))

    # list of tuples used to feed the loop below. Contains all the necessary elements for each parameter checkbox
    l_tmpList = [
        # the substitution is because some labels have '·' instead of ' ' in order to separate words
        (se3_utilities.get_user_string(p_context, 'sv_AllVersions'),
         p_context['a'],
         se3_utilities.g_svAllVersions),
        (se3_utilities.get_user_string(p_context, 'm_DisplayLxx'),
         p_context['x'],
         se3_utilities.g_svDisplayLxx),
        (se3_utilities.get_user_string(p_context, 'm_DisplayNasb'),
         p_context['n'],
         se3_utilities.g_svDisplayNasb),
        (se3_utilities.get_user_string(p_context, 'm_DisplayKJV'),
         p_context['k'],
         se3_utilities.g_svDisplayKjv),
        (se3_utilities.get_user_string(p_context, 'p_displayGround'),
         p_context['g'],
         se3_utilities.g_pDisplayGround),
        (se3_utilities.get_user_string(p_context, 'p_parallelVersions'),
         p_context['r'],
         se3_utilities.g_pParallel)
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


# ---------------------- Table of contents response generation ---------------------------------------------------------
# not isolated in a separate module
def get_toc(p_previousContext, p_context, p_dbConnectionPool):
    g_loggerSE3.info('Getting TOC response')
    g_loggerSE3.debug('p_previousContext: {0}'.format(p_previousContext))
    g_loggerSE3.debug('p_context: {0}'.format(p_context))

    l_dbConnection = p_dbConnectionPool.getConnection()

    l_response = ''

    # Ta1 : Quran, surah number order
    # Ta2 : Quran, revelation order
    # Tb  : NT
    # Tc  : OT
    # T   : all scripture

    # For Quran, chapter ordering based on ST_ORDER (Surah number) or ST_ORDER_ALT (Revelation order)
    if p_context['K'] == 'Ta1':
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
    elif p_context['K'] == 'Ta2':
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
        if p_context['K'] == 'Tb':
            l_cond = 'ID_GROUP_0 = "NT"'
            # title for NT
            l_response += '<h1 class="TocTitle">{0}</h1>\n'.format(
                se3_utilities.get_user_string(p_context, 'm_tocNTTitle')
            )
        elif p_context['K'] == 'Tc':
            l_cond = 'ID_GROUP_0 = "OT"'
            # title for OT
            l_response += '<h1 class="TocTitle">{0}</h1>\n'.format(
                se3_utilities.get_user_string(p_context, 'm_tocOTTitle')
            )
        else:
            l_cond = 'true'
            # title for All scripture
            l_response += '<h1 class="TocTitle">{0}</h1>\n'.format(
                se3_utilities.get_user_string(p_context, 'm_tocAllTitle')
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

    g_loggerSE3.debug('l_query: {0}'.format(l_query))
    try:
        l_cursor = l_dbConnection.cursor(buffered=True)
        l_cursor.execute(l_query)

        # Quran only (2 columns with Surah names)
        if p_context['K'][0:2] == 'Ta':
            # title for Quran (depending on Surah order)
            l_response += '<h1 class="TocTitle">{0}</h1><div class="QuranToc"><div class="QuranTocCol1">\n'.format(
                se3_utilities.get_user_string(p_context, 'm_tocQuranTitle') if p_context['K'] == 'Ta1'else
                se3_utilities.get_user_string(p_context, 'm_tocQuranTitleRev')
            )

            l_chapterCount = 1
            for l_chapter, l_nameOr, l_nameOr2, l_nameEn, l_nameFr in l_cursor:
                l_response += ('<p class="QuranSurah"><a href="" class="svGoPassage" newBook="Qur" ' +
                               'newChapter="{0}" newVerse1="1" newVerse2="x">{0}</a>: {1} - {2}</p>\n').format(
                    l_chapter,
                    l_nameFr if p_context['z'] == 'fr' else l_nameEn,
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
                l_chapLinks = ''
                for i in range(1, l_chapterCount+1):
                    l_chapLinks += ('<a href="" class="svGoPassage" newBook="{0}" ' +
                                    'newChapter="{1}" newVerse1="1" newVerse2="x">{1}</a>\n').format(l_bookId, i)

                l_response += '<p class="TocBook">{0}: {1}</p>\n'.format(
                    l_nameFr if p_context['z'] == 'fr' else l_nameEn, l_chapLinks
                )

        l_cursor.close()

    except Exception as l_exception:
        g_loggerSE3.warning('Something went wrong {0}'.format(l_exception.args))

    p_dbConnectionPool.releaseConnection(l_dbConnection)

    return l_response, p_context
