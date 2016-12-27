# -*- coding: utf-8 -*-

import os
from ec_local_param import *

__author__ = 'fi11222'

class EcAppParam:
    # transfer of local params from LocalParam to EcAppParam
    gcm_appDomain = LocalParam.gcm_appDomain
    gcm_httpPort = LocalParam.gcm_httpPort
    gcm_dbServer = LocalParam.gcm_dbServer
    gcm_dbUserLocal = LocalParam.gcm_dbUserLocal
    gcm_dbPasswordLocal = LocalParam.gcm_dbPasswordLocal
    gcm_debugModeOn = LocalParam.gcm_debugModeOn
    gcm_verboseModeOn = LocalParam.gcm_verboseModeOn
    gcm_skipBrowscap = LocalParam.gcm_skipBrowscap
    gcm_allConnectionsReport = LocalParam.gcm_allConnectionsReport
    gcm_mailSender = LocalParam.gcm_mailSender
    gcm_smtpServer = LocalParam.gcm_smtpServer
    gcm_amazonSmtp = LocalParam.gcm_amazonSmtp
    gcm_sesIamUser = LocalParam.gcm_sesIamUser
    gcm_sesUserName = LocalParam.gcm_sesUserName
    gcm_sesPassword = LocalParam.gcm_sesPassword
    gcm_gmailSmtp = LocalParam.gcm_gmailSmtp
    gcm_gmailPassword = LocalParam.gcm_gmailPassword
    gcm_appRoot = LocalParam.gcm_appRoot

    # Static files root
    gcm_staticRoot = LocalParam.gcm_appRoot

    # general parameters
    gcm_appName = 'ScriptureEngineIII'
    gcm_appVersion = '3.4.2a'
    gcm_appTitle = 'Scripture Search Engine III'

    # HTTP server parameters

    # in days (100 years)
    gcm_cookiePersistence = 365*100

    # Session name (cookie name for session handling)
    gcm_sessionName = 'ECTerminalID_{0}'.format(gcm_appName)

    # Database parameters
    gcm_dbDatabase = 'ScriptureEngineIII'
    gcm_dbUser = gcm_dbUserLocal
    gcm_dbPassword = gcm_dbPasswordLocal

    # size of DB connection pool + on/off switch
    gcm_noConnectionPool = True
    gcm_connectionPoolCount = 120

    # average db connection life span (in hours)
    gcm_dbcLifeAverage = 2

    # Logging
    gcm_mailRecipients = ['nicolas.reimen@gmail.com', 'nrtmp@free.fr']
    gcm_logFile = os.path.join(gcm_appRoot, 'Log/ec_log.csv')

    # Templates
    gcm_templateBrowserTest = os.path.join(gcm_appRoot, 'Templates/browser_test.html')
    gcm_templateBadBrowser = os.path.join(gcm_appRoot, 'Templates/bad_browser.html')

    # Browscap
    gcm_browscapUrl = 'http://browscap.org/stream?q=BrowsCapCSV'
    gcm_browscapLatestVersionUrl = 'http://browscap.org/version-number'
    gcm_browscapLocalFile = os.path.join(gcm_appRoot, 'browscap_latest.csv')

    # Multi Language
    @classmethod
    def i18n(cls, k):
        return cls.gcm_userStrings[k]

    gcm_userStrings = {
        'en-m_unselectAll': 'Unselect All',
        'fr-m_unselectAll': 'Tout Décocher',
        'en-m_CollapsarShow': '⇣',
        'fr-m_CollapsarShow': '⇣',
        'en-m_CollapsarHide': '⇡',
        'fr-m_CollapsarHide': '⇡',
        'en-m_ApplyLabel': 'Apply',
        'fr-m_ApplyLabel': 'Appliquer',
        'en-m_lexLex': 'Lexicon',
        'fr-m_lexLex': 'Lexique',
        'en-m_lexArabic': 'Arabic',
        'fr-m_lexArabic': 'Arabe',
        'en-m_lexGreek': 'Greek',
        'fr-m_lexGreek': 'Grec',
        'en-m_lexHebrew': 'Hebrew',
        'fr-m_lexHebrew': 'Hébreu',
        'en-m_tocAllTitle': 'Table of Contents - All Scripture',
        'fr-m_tocAllTitle': 'Table des matières - Toutes les écritures',
        'en-m_tocOTTitle': 'Table of Contents - Old Testament',
        'fr-m_tocOTTitle': 'Table des matières - Ancien testament',
        'en-m_tocNTTitle': 'Table of Contents - New Testament',
        'fr-m_tocNTTitle': 'Table des matières - Nouveau Testament',
        'en-m_tocQuranTitle': 'Table of Contents - Surahs of the Qur\'an (Final Testament)',
        'fr-m_tocQuranTitle': 'Table des matières - Sourates du Coran (Testament final)',
        'en-m_tocQuranTitleRev': """
            Table of Contents - Surahs of the Qur\'an (Final Testament)<br/>
            <span style="font-size: smaller;">Revelation Order</span>
            """,
        'fr-m_tocQuranTitleRev': """
            Table des matières - Sourates du Coran (Testament final)<br/>
            <span style="font-size: smaller;">Ordre de la révélation</span>
            """,
        'en-m_tocQuranRev': 'Qur\'an <span style="font-size: smaller;">(Revelation Order)</span>',
        'fr-m_tocQuranRev': 'Coran <span style="font-size: smaller;">(Ordre de la révélation)</span>',
        'en-m_tocToc': 'Contents',
        'fr-m_tocToc': 'Table',
        'en-m_tocAllScripture': 'All Scripture',
        'fr-m_tocAllScripture': 'Toutes les écritures',
        'en-m_DisplayLxx': 'Display LXX Interlinear',
        'fr-m_DisplayLxx': 'Affichage interlinéaire LXX',
        'en-m_DisplayKJV': 'Display KJV Interlinear',
        'fr-m_DisplayKJV': 'Affichage interlinéaire KJV',
        'en-m_DisplayNasb': 'Display NASB Interlinear',
        'fr-m_DisplayNasb': 'Affichage interlinéaire NASB',
        'en-m_paramControl': 'Parameters',
        'fr-m_paramControl': 'Paramètres',
        'en-m_bible': 'Bible',
        'fr-m_bible': 'Bible',
        'en-m_quran': 'Qur\'an',
        'fr-m_quran': 'Coran',
        'en-m_bibleVersions': 'Bible Versions',
        'fr-m_bibleVersions': 'Traductions de la Bible',
        'en-m_quranVersions': 'Quran Versions',
        'fr-m_quranVersions': 'Traductions du Coran',
        'en-m_labelSearch': 'Search',
        'fr-m_labelSearch': 'Rechercher',
        'en-m_labelWholeWords': 'Whole Words',
        'fr-m_labelWholeWords': 'Mots entiers',
        'en-m_labelCaseSensitive': 'Case Sensitive',
        'fr-m_labelCaseSensitive': 'Dépendant de la Casse',
        'en-m_labelExclude': 'Exclude',
        'fr-m_labelExclude': 'Exclure',
        'en-m_labelSearchMode': 'Search Mode',
        'fr-m_labelSearchMode': 'Mode de Recherche',
        'en-m_labelSearchMode0': 'All words (AND)',
        'fr-m_labelSearchMode0': 'Tous les mots (ET)',
        'en-m_labelSearchMode1': 'Any word (OR)',
        'fr-m_labelSearchMode1': 'Au moins un mot (OU)',
        'en-m_labelSearchMode2': 'Exact Phrase',
        'fr-m_labelSearchMode2': 'Chaîne exacte',
        'en-m_labelSearchScope': 'Search Scope',
        'fr-m_labelSearchScope': 'Périmètre',
        'en-m_labelSearchScopeQ': 'Quran',
        'fr-m_labelSearchScopeQ': 'Coran',
        'en-m_labelSearchScopeQ0': 'All',
        'fr-m_labelSearchScopeQ0': 'Tout',
        'en-m_labelSearchScopeQ1': 'No',
        'fr-m_labelSearchScopeQ1': 'Non',
        'en-m_labelSearchScopeNT0': 'All',
        'fr-m_labelSearchScopeNT0': 'Tout',
        'en-m_labelSearchScopeNT1': 'Gospel and Acts',
        'fr-m_labelSearchScopeNT1': 'Évangiles et Actes',
        'en-m_labelSearchScopeNT2': 'Epistles',
        'fr-m_labelSearchScopeNT2': 'Épîtres',
        'en-m_labelSearchScopeNT3': 'Revelation',
        'fr-m_labelSearchScopeNT3': 'Apocalypse',
        'en-m_labelSearchScopeNT4': 'No',
        'fr-m_labelSearchScopeNT4': 'Non',
        'en-m_labelSearchScopeNT': 'New Testament',
        'fr-m_labelSearchScopeNT': 'Nouveau Testament',
        'en-m_labelSearchScopeOT': 'Old Testament',
        'fr-m_labelSearchScopeOT': 'Ancien Testament',
        'en-m_labelSearchScopeOT0': 'All',
        'fr-m_labelSearchScopeOT0': 'Tout',
        'en-m_labelSearchScopeOT1': 'Pentateuch',
        'fr-m_labelSearchScopeOT1': 'Pentateuch',
        'en-m_labelSearchScopeOT2': 'History',
        'fr-m_labelSearchScopeOT2': 'Histoire',
        'en-m_labelSearchScopeOT3': 'Wisdom',
        'fr-m_labelSearchScopeOT3': 'Sagesse',
        'en-m_labelSearchScopeOT4': 'Prophets',
        'fr-m_labelSearchScopeOT4': 'Prophètes',
        'en-m_labelSearchScopeOT5': 'No',
        'fr-m_labelSearchScopeOT5': 'Non',

        'en-s_limitMessage': 'Only the first {0} verses are displayed. In order to display the rest (max. {1}) click:',
        'fr-s_limitMessage': 'Seuls les {0} premiers versets sont affichés. Pour voir les suivants (max. {1}) cliquer:',
        'en-s_displayAll': 'All Verses',
        'fr-s_displayAll': 'Tous les résultats',
        'en-s_report1singular': 'verse containing',
        'fr-s_report1singular': 'verset contenant',
        'en-s_report1plural': 'verses containing',
        'fr-s_report1plural': 'versets contenant',
        'en-s_report2phrase': 'the phrase',
        'fr-s_report2phrase': 'la chaîne',
        'en-s_report2singular': 'the word',
        'fr-s_report2singular': 'le mot',
        'en-s_report2plural': 'the words',
        'fr-s_report2plural': 'les mots',
        'en-s_report3singular': 'but not the word',
        'fr-s_report3singular': 'mais non le mot',
        'en-s_report3plural': 'but not the words',
        'fr-s_report3plural': 'mais non les mots',
        'en-s_report4singular': 'in version',
        'fr-s_report4singular': 'dans la traduction suivante:',
        'en-s_report4plural': 'in versions',
        'fr-s_report4plural': 'dans les traductions suivantes:',
        'en-s_and': 'and',
        'fr-s_and': 'et',
        'en-s_or': 'or',
        'fr-s_or': 'ou',
        'en-s_caseSensitive': 'Case Sensitive',
        'fr-s_caseSensitive': 'en tenant compte de la casse',
        'en-s_caseInsensitive': 'Case Insensitive',
        'fr-s_caseInsensitive': 'sans tenir compte de la casse',
        'en-s_wholeWords': 'Whole Words',
        'fr-s_wholeWords': 'mots entiers',
        'en-s_scope': 'Scope',
        'fr-s_scope': 'Périmètre',
        'en-s_scopeQuran': 'Quran',
        'fr-s_scopeQuran': 'Coran',
        'en-s_scopeNT': 'New Testament',
        'fr-s_scopeNT': 'Nouveau Testament',
        'en-s_scopeNTGospelA': 'Gospel and Acts',
        'fr-s_scopeNTGospelA': 'Évangiles et actes',
        'en-s_scopeNTEpi': 'Epistles',
        'fr-s_scopeNTEpi': 'Épîtres',
        'en-s_scopeNTRev': 'Revelation',
        'fr-s_scopeNTRev': 'Apocalypse',
        'en-s_scopeOT': 'Old Testament',
        'fr-s_scopeOT': 'Ancien Testament',
        'en-s_scopeOTPentateuch': 'Pentateuch',
        'fr-s_scopeOTPentateuch': 'Pentateuch',
        'en-s_scopeOTHist': 'History Books',
        'fr-s_scopeOTHist': 'Livres historiques',
        'en-s_scopeOTWis': 'Wisdom',
        'fr-s_scopeOTWis': 'Livres de sagesse',
        'en-s_scopeOTPro': 'Prophets',
        'fr-s_scopeOTPro': 'Prophètes',

        'en-p_parallelVersions': 'Display·in·Parallel',
        'fr-p_parallelVersions': 'Affichage·en·parallèle',
        'en-p_stackedVersions': 'Stacked·Display',
        'fr-p_stackedVersions': 'Affichage·en·succession',
        'en-p_displayGround': 'Display·Ground·Text',
        'fr-p_displayGround': 'Afficher·le·texte·original',
        'en-p_hideGround': 'Hide·Ground·Text',
        'fr-p_hideGround': 'Masquer·le·texte·original',
        'en-p_VerseWord': 'verse',
        'fr-p_VerseWord': 'verset',
        'en-p_VerseTo': 'to',
        'fr-p_VerseTo': 'à',
        'en-p_GroundText': 'Ground·Text',
        'fr-p_GroundText': 'Texte·original',
        'en-p_PreviousLink': 'Previous Chapter',
        'fr-p_PreviousLink': 'Chapitre précédent',
        'en-p_NextLink': 'Next Chapter',
        'fr-p_NextLink': 'Chapitre suivant',
        'en-p_noText': 'No text for this version',
        'fr-p_noText': 'Pas de texte pour cette traduction',

        'en-w_translation': 'Translation',
        'fr-w_translation': 'Traduction',
        'en-w_homonymousRoot': 'Homonymous Root',
        'fr-w_homonymousRoot': 'Racine homonyme',
        'en-w_homonymousRoots': 'Homonymous Roots',
        'fr-w_homonymousRoots': 'Racines homonymes',
        'en-w_allRoots': 'All Roots',
        'fr-w_allRoots': 'Toutes les racines',
        'en-w_root': 'Root',
        'fr-w_root': 'Racine',
        'en-w_type': 'Word Type',
        'fr-w_type': 'Type',
        'en-w_OccurencesTitle': 'Occurences',
        'fr-w_OccurencesTitle': 'Occurences',
        'en-w_grammarLong': 'Grammar',
        'fr-w_grammarLong': 'Grammaire',
        'en-w_definition': 'Definition',
        'fr-w_definition': 'Définition',
        'en-w_derivation': 'Etymology',
        'fr-w_derivation': 'Étymologie',
        'en-w_freqABible': 'Translation Frequencies (KJV)',
        'fr-w_freqABible': 'Occurences (KJV)',
        'en-w_freqAQuran': 'Translation Frequencies (A)',
        'fr-w_freqAQuran': 'Occurences (A)',
        'en-w_freqBBible': 'Translation Frequencies (NASB)',
        'fr-w_freqBBible': 'Occurences (NASB)',
        'en-w_freqBQuran': 'Translation Frequencies (B)',
        'fr-w_freqBQuran': 'Occurences (B)',
        'en-w_limitMessage':
            'Only the first {0} occurences are displayed. In order to display the rest (max. {1}) click:',
        'fr-w_limitMessage': """
            Seuls les {0} premières occurences sont affichées. Pour voir les suivantes (max. {1}) cliquer:
        """,
        'en-w_displayAll': 'All Occurences',
        'fr-w_displayAll': 'Toutes les occurences',
        'en-w_hardLimitMessage': 'Only the first {0} occurences are displayed.',
        'fr-w_hardLimitMessage': 'Seuls les {0} premières occurences sont affichées.',

        'en-sv_wholeChapter': 'Whole·Chapter',
        'fr-sv_wholeChapter': 'Tout·le·chapitre',
        'en-sv_wholeSurah': 'Whole·Surah',
        'fr-sv_wholeSurah': 'Toute·la·sourate',
        'en-sv_5Neighborhood': '5·closest·verses',
        'fr-sv_5Neighborhood': '5·versets·adjacents',
        'en-sv_9Neighborhood': '9·closest·verses',
        'fr-sv_9Neighborhood': '9·versets·adjacents',
        'en-sv_TranslationsTitle': 'Translations',
        'fr-sv_TranslationsTitle': 'Traductions',
        'en-sv_PreviousLink': 'Previous Verse',
        'fr-sv_PreviousLink': 'Verset précédent',
        'en-sv_NextLink': 'Next Verse',
        'fr-sv_NextLink': 'Verset suivant',
        'en-sv_DisplayNasb': '+NASB',
        'fr-sv_DisplayNasb': '+NASB',
        'en-sv_HideNasb': 'Hide NASB',
        'fr-sv_HideNasb': 'Masquer NASB',
        'en-sv_DisplayLxx': '+LXX',
        'fr-sv_DisplayLxx': '+LXX',
        'en-sv_HideLxx': 'Hide LXX',
        'fr-sv_HideLxx': 'Masquer LXX',
        'en-sv_DisplayKjv': '+KJV',
        'fr-sv_DisplayKjv': '+KJV',
        'en-sv_HideKjv': 'Hide KJV',
        'fr-sv_HideKjv': 'Masquer KJV',
        'en-sv_AllVersions': 'All·Versions',
        'fr-sv_AllVersions': 'Toutes·les·traductions',
        'en-sv_SelectedVersions': 'Selected·Versions',
        'fr-sv_SelectedVersions': 'Traductions·sélectionnées',

        'en-e_wrongV2Passage': """
            <p>
                <span class="ErrHigh">Error</span>: Incorrect passage reference (incorrect V2):
                {0} {1}:{2}-<b>{3}</b>
            </p>
        """,
        'fr-e_wrongV2Passage': """
            <p>
                <span class="ErrHigh">Erreur</span>: Référence de passage incorrecte (V2 erroné):
                {0} {1}:{2}-<b>{3}</b>
            </p>
        """,

        'en-e_wrongV1Passage': """
            <p>
                <span class="ErrHigh">Error</span>: Incorrect passage reference (incorrect V1):
                {0} {1}:<b>{2}</b>-{3}
            </p>
        """,
        'fr-e_wrongV1Passage': """
            <p>
                <span class="ErrHigh">Erreur</span>: Référence de passage incorrecte (V1 erroné):
                {0} {1}:<b>{2}</b>-{3}
            </p>
        """,

        'en-e_wrongChapterPassage': """
            <p>
                <span class="ErrHigh">Error</span>: Incorrect passage reference (incorrect chapter number):
                {0} <b>{1}</b>:{2}-{3}
            </p>
        """,
        'fr-e_wrongChapterPassage': """
            <p>
                <span class="ErrHigh">Erreur</span>: Référence de passage incorrecte (chapitre erroné):
                {0} <b>{1}</b>:{2}-{3}
            </p>
        """,

        'en-e_wrongBookPassage': """
            <p>
                <span class="ErrHigh">Error</span>: Incorrect passage reference (non-existent book):
                <b>{0}</b> {1}:{2}-{3}
            </p>
        """,
        'fr-e_wrongBookPassage': """
            <p>
                <span class="ErrHigh">Erreur</span>: Référence de passage incorrecte (livre inconnu):
                <b>{0}</b> {1}:{2}-{3}
            </p>
        """,

        'en-e_wrongVVerse': """
            <p>
                <span class="ErrHigh">Error</span>: Incorrect verse reference (incorrect verse number):
                {0} {1}:<b>{2}</b>
            </p>
        """,
        'fr-e_wrongVVerse': """
            <p>
                <span class="ErrHigh">Erreur</span>: Référence de verset incorrecte (numéro de verset erroné):
                {0} {1}:<b>{2}</b>
            </p>
        """,

        'en-e_wrongChapterVerse': """
            <p>
                <span class="ErrHigh">Error</span>: Incorrect verse reference (incorrect chapter number):
                {0} <b>{1}</b>:{2}
            </p>
        """,
        'fr-e_wrongChapterVerse': """
            <p>
                <span class="ErrHigh">Erreur</span>: Référence de verset incorrecte (chapitre erroné):
                {0} <b>{1}</b>:{2}
            </p>
        """,

        'en-e_wrongBookVerse': """
            <p>
                <span class="ErrHigh">Error</span>: Incorrect verse reference (non-existent book):
                <b>{0}</b> {1}:{2}
            </p>
        """,
        'fr-e_wrongBookVerse': """
            <p>
                <span class="ErrHigh">Erreur</span>: Référence de verset incorrecte (livre inconnu):
                <b>{0}</b> {1}:{2}
            </p>
        """,

        'en-e_wrongIdWord': """
            <p>
                <span class="ErrHigh">Error</span>: Incorrect word reference (malformed word ID):
                {0} {1}:{2} [<b>{3}</b>]
            </p>
        """,
        'fr-e_wrongIdWord': """
            <p>
                <span class="ErrHigh">Erreur</span>: Référence de mot incorrecte (identifiant de mot mal formé):
                {0} {1}:{2} [<b>{3}</b>]
            </p>
        """,

        'en-e_wrongVWord': """
            <p>
                <span class="ErrHigh">Error</span>: Incorrect word reference (incorrect verse number):
                {0} {1}:<b>{2}</b>.{3} [{4} {5}]
            </p>
        """,
        'fr-e_wrongVWord': """
            <p>
                <span class="ErrHigh">Erreur</span>: Référence de mot incorrecte (numéro de verset erroné):
                {0} {1}:<b>{2}</b>.{3} [{4} {5}]
            </p>
        """,

        'en-e_wrongChapterWord': """
            <p>
                <span class="ErrHigh">Error</span>: Incorrect word reference (incorrect chapter number):
                {0} <b>{1}</b>:{2}.{3} [{4} {5}]
            </p>
        """,
        'fr-e_wrongChapterWord': """
            <p>
                <span class="ErrHigh">Erreur</span>: Référence de mot incorrecte (chapitre erroné):
                {0} <b>{1}</b>:{2}.{3} [{4} {5}]
            </p>
        """,

        'en-e_wrongBookWord': """
            <p>
                <span class="ErrHigh">Error</span>: Incorrect word reference (non-existent book):
                <b>{0}</b> {1}:{2}.{3} [{4} {5}]
            </p>
        """,
        'fr-e_wrongBookWord': """
            <p>
                <span class="ErrHigh">Erreur</span>: Référence de mot incorrecte (livre inconnu):
                <b>{0}</b> {1}:{2}.{3} [{4} {5}]
            </p>
        """,

        'en-e_wrongWordWord': """
            <p>
                <span class="ErrHigh">Error</span>: Incorrect word reference (non-numeric word number):
                {0} {1}:{2}.<b>{3}</b> [{4} {5}]
            </p>
        """,
        'fr-e_wrongWordWord': """
            <p>
                <span class="ErrHigh">Erreur</span>: Référence de mot incorrecte (numéro de mot invalide):
                {0} {1}:{2}.<b>{3}</b> [{4} {5}]
            </p>
        """,

        'en-e_wrongRoot': """
            <p>
                <span class="ErrHigh">Error</span>: Incorrect root reference: <b>{0}</b>
            </p>
        """,
        'fr-e_wrongRoot': """
            <p>
                <span class="ErrHigh">Erreur</span>: Référence de racine incorrecte: <b>{0}</b>
            </p>
        """,

        'en-e_noRoot': """
            <p>
                <span class="ErrHigh">Error</span>: No root with this reference: <b>{0}</b>
            </p>
        """,
        'fr-e_noRoot': """
            <p>
                <span class="ErrHigh">Erreur</span>: Référence de racine inconnue: <b>{0}</b>
            </p>
        """,

        'en-e_noWord': """
            <p>
                <span class="ErrHigh">Error</span>: No lexicon entry corresponding to this Word ID: <b>{0}</b>
            </p>
        """,
        'fr-e_noWord': """
            <p>
                <span class="ErrHigh">Erreur</span>: Aucune entrée dans le lexique ne correspond
                à cet identifiant: <b>{0}</b>
            </p>
        """,

        'en-e_noPassage': """
            <p>
                <span class="ErrHigh">Error</span>: No scripture passage corresponds to these Parameters:
                <table>
                <tr><td>Book:</td><td>{0}</td></tr>
                <tr><td>Chapter:</td><td>{1}</td></tr>
                </table>
            </p>
        """,
        'fr-e_noPassage': """
            <p>
                <span class="ErrHigh">Error</span>: Aucun passage Ne correspond à ces paramètres:
                <table>
                <tr><td>Book:</td><td>{0}</td></tr>
                <tr><td>Chapter:</td><td>{1}</td></tr>
                </table>
            </p>
        """,

        'en-TestingBrowserMsg': """
            The application is testing the capabilities of your browser ...
        """,
        'fr-TestingBrowserMsg': """
            L'application teste les caractéristiques de votre navigateur ...
        """,
        'en-GainAccess1Msg': """
            If you are not redirected within 30 seconds, please enable JavaScript and Cookies then click on
        """,
        'fr-GainAccess1Msg': """
            Si vous n'êtes pas redirigé dans les 30 secondes, merci d'activer JavaScript et les cookies puis cliquer
        """,

        'en-BadBrowserMsg': """
            <span class="ErrHigh">Incompatible Browser</span>: Your browser does not currently have
            the required capabilities to use Scripture Search Engine III.
        """,
        'fr-BadBrowserMsg': """
            <span class="ErrHigh">Navigateur incompatible</span>: Votre navigateur ne possède pas les caractéristiques
            requises pour utiliser Scripture Search Engine III
        """,
        'en-GainAccessMsg': """
            In order to gain access to the application, please enable JavaScript and Cookies then click on
        """,
        'fr-GainAccessMsg': """
            Pour accéder à l'application, merci d'activer JavaScript et les cookies puis cliquer
        """,

        'en-ThisLinkMsg': 'This Link',
        'fr-ThisLinkMsg': 'ce lien'
    }

