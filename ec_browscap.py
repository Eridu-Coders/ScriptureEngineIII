# -*- coding: utf-8 -*-

import traceback
import warnings
import sre_constants
import locale
import csv
import re

import logging

import urllib.request
import urllib.error

from datetime import datetime

from ec_app_params import *

__author__ = 'fi11222'

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

# log = logging.getLogger(__name__)

log = logging.getLogger(g_appName + '.browscap')
if g_verboseModeOn:
    log.setLevel(logging.INFO)

TYPE_CSV = 1


# ----------------------------------------------------------------------------------------------------------------------
class BrowscapError(Exception):
    """Base pybrowscap Error."""

    def __init__(self, value, e):
        s = StringIO()
        traceback.print_exc(file=s)
        self.value = (value, s.getvalue())
        s.close()

    def __str__(self):
        return repr(self.value)


# ----------------------------------------------------------------------------------------------------------------------
def load_browscap_file(browscap_file_path):
    """
    Loading browscap csv data file, parsing in into accessible python
    form and returning a new Browscap class instance with all appropriate data.

    :param browscap_file_path: location of browcap file on filesystem
    :type browscap_file_path: string
    :returns: Browscap instance filled with data
    :rtype: pybrowscap.loader.Browscap

    """
    def replace_defaults(line, defaults):
        """Replaces 'default' values for a line with parent line value and converting it into native python value.

        :param line: original line from browscap file
        :type line: dict
        :param defaults: default values for current line
        :type defaults: dict
        :returns: dictionary with replaced default values
        :rtype: dict
        :raises: IOError

        """
        new_line = {}
        for feature, value in line.items():
            if value == 'default' or value == '':
                value = defaults[feature]
            if value == 'true':
                value = True
            if value == 'false':
                value = False
            if feature == 'MinorVer' and value == '0':
                value = defaults[feature]
            if feature == 'MajorVer' or feature == 'MinorVer':
                try:
                    value = int(value)
                except (ValueError, OverflowError):
                    value = 0
            if (feature == 'Version' or feature == 'RenderingEngine_Version') and value == '0':
                value = defaults[feature]
            if (feature == 'CSSVersion' or feature == 'AolVersion' or feature == 'Version' or
                feature == 'RenderingEngine_Version' or feature == 'Platform_Version'):
                try:
                    value = float(value)
                except (ValueError, OverflowError):
                    value = float(0)
            new_line[feature.lower()] = value
        return new_line
        # end of replace_defaults() ------------------------------------------------------------------------------------

    try:
        with open(browscap_file_path, 'r') as csvfile:
            log.warning('Loading Browscap local source file %s', browscap_file_path)

            # figures out the CSV parameters (field sep, string delimiter, ...) hopefully
            dialect = csv.Sniffer().sniff(csvfile.read(4096))

            # Goes back to begining of file
            csvfile.seek(0)
            log.info('Getting file version and release date')

            # skip top line with "GJK_Browscap_Version","GJK_Browscap_Version"
            csvfile.readline()

            # Determines Browscap file version -------------------------------------------------------------------------

            line = next(csv.reader(StringIO(csvfile.readline()), dialect=dialect))
            # this gets the SECOND line of the file (the first was skipped)
            version = None
            try:
                version = int(line[0])
                log.info('Local browcap file version: {0}'.format(version))
            except ValueError:
                log.exception('Error while getting browscap file version')

            # Determines Browscap file release date --------------------------------------------------------------------
            old_locale = locale.getlocale()
            release_date = None
            try:
                locale.setlocale(locale.LC_TIME, locale.normalize('en_US.utf8'))
                release_date = datetime.strptime(line[1][:-6], '%a, %d %b %Y %H:%M:%S')
                log.info('Local browscap file release date: {0}'.format(release_date))
            except (ValueError, locale.Error):
                log.exception('Error while getting browscap file release date')
            finally:
                locale.setlocale(locale.LC_TIME, old_locale)

            # Start reading data rows ----------------------------------------------------------------------------------
            # the csv lib starts at the THRID line of the file, reads the column headers and then the rows one by one
            log.info('Reading browscap user-agent data')
            reader = csv.DictReader(csvfile, dialect=dialect)
            defaults = {}
            browscap_data = {}
            regex_cache = []
            for line in reader:
                if line['Parent'] == '':
                    # This is the "Default of the Defaults" top line of the file -- Not used
                    continue
                if line['Parent'] == 'DefaultProperties':
                    # This is the default line for each group of UserAgents --> Stored in defaults
                    defaults = line
                    continue

                line = replace_defaults(line, defaults)

                if len(regex_cache) % 50000 == 0 and len(regex_cache) > 0:
                    log.warning('50 000 rows loaded from Browscap local source file %s', browscap_file_path)

                # Progress message in case verbose mode is on
                if g_verboseModeOn:
                    print('   Rows read:', len(regex_cache), end='\r' )

                try:
                    ua_regex = '^{0}$'.format(re.escape(line['propertyname']))
                    ua_regex = ua_regex.replace('\\?', '.').replace('\\*', '.*?')
                    browscap_data[ua_regex] = line
                    log.debug('Compiling user agent regex: %s', ua_regex)
                    regex_cache.append(re.compile(ua_regex))
                except sre_constants.error:
                    continue

            # End of progress message in case verbose mode is on
            if g_verboseModeOn:
                print()
        return Browscap(browscap_data, regex_cache, browscap_file_path, TYPE_CSV,
                        version, release_date)
    except IOError:
        log.exception('Error while reading browscap source file %s', browscap_file_path)
        raise


# ----------------------------------------------------------------------------------------------------------------------
class Browser(object):
    """Browser class represents one record in  browscap data file."""

    def __init__(self, user_agent):
        self.user_agent = user_agent

    def items(self):
        return self.user_agent.copy()

    def get(self, feature, default=None):
        return self.user_agent.get(feature, default)

    def name(self):
        return self.get('browser')

    def category(self):
        return self.get('parent')

    def platform(self):
        return self.get('platform')

    def aol_version(self):
        return self.get('aolversion')

    def version(self):
        return self.get('version')

    def version_major(self):
        return self.get('majorver', 0)

    def version_minor(self):
        return self.get('minorver', 0)

    def css_version(self):
        return self.get('cssversion', 0)

    def rendering_engine_name(self):
        return self.get('renderingengine_name')

    def rendering_engine_version(self):
        return self.get('renderingengine_version')

    def device_maker(self):
        return self.get('device_maker')

    def device_name(self):
        return self.get('device_name')

    def platform_description(self):
        return self.get('platform_description')

    def platform_version(self):
        return self.get('platform_version')

    def litemode(self):
        return self.get('litemode')

    def supports(self, feature):
        to_return = self.get(feature, False)
        if isinstance(to_return, bool):
            return to_return
        else:
            return False

    def supports_tables(self):
        return self.supports('tables')

    def supports_frames(self):
        return self.supports('frames')

    def supports_iframes(self):
        return self.supports('iframes')

    def supports_java(self):
        return self.supports('javaapplets')

    def supports_javascript(self):
        return self.supports('javascript')

    def supports_vbscript(self):
        return self.supports('vbscript')

    def supports_activex(self):
        return self.supports('activexcontrols')

    def supports_cookies(self):
        return self.supports('cookies')

    def supports_css(self):
        return self.css_version() > 0

    def is_crawler(self):
        return self.supports('crawler')

    def is_mobile(self):
        return self.supports('ismobiledevice')

    def is_syndication_reader(self):
        return self.supports('issyndicationreader')

    def is_banned(self):
        warnings.warn(u'This field was removed from csv browscap file', DeprecationWarning, stacklevel=2)
        return None

    def is_alpha(self):
        return self.supports('alpha')

    def is_beta(self):
        return self.supports('beta')

    def features(self):
        features = []
        for feature in ['tables', 'frames', 'iframes', 'javascript', 'vbscript', 'cookies']:
            if self.supports(feature) is True:
                features.append(feature)
        if self.supports_activex():
            features.append('activex')
        if self.supports_java():
            features.append('java')
        if self.css_version() > 0:
            features.append('css1')
        if self.css_version() > 1:
            features.append('css2')
        if self.css_version() > 2:
            features.append('css3')
        return features


# ----------------------------------------------------------------------------------------------------------------------
class Downloader(object):
    """
    This class is responsible for downloading new versions of browscap file.
    It is possible to to define a timeout for connection and proxy server settings.

    """

    def __init__(self, url_version, url_file, timeout=120, proxy=None, additional_handlers=None):
        """Constructor

        Args:

        :param url: URL of browscap file
        :type url: string
        :param timeout: connection timeout
        :type timeout: int
        :param proxy: url of proxy server
        :type proxy: string
        :param additional_handlers: list of additional urllib2 handlers
        :type additional_handlers: list
        :returns: Downloader instance
        :rtype: Downloader

        """
        self.url_version = url_version
        self.url_file = url_file
        self.timeout = timeout
        self.proxy = proxy
        self.additional_handlers = additional_handlers

    def get(self, save_to_file_path=None):
        """
        Getting browscap file contents and saving it to file or returning it as a string.
        Returns file contents if save_to_file_path is not None, file contents as string otherwise.

        ;param save_to_file_path: path on filesystem where browscap file will be saved
        :type save_to_file_path: string
        :returns: None or browscap file contents
        :rtype: string
        :raises: ValueError, urllib2.URLError, urllib2.HTTPError

        """
        if save_to_file_path is None:
            log.warning('No local file path given - exiting')
            return

        # --------------------- Getting version number of local file (if any) ------------------------------------------
        local_version = None
        try:
            with open(save_to_file_path, 'r') as csvfile:
                log.info('Reading browscap version from local file %s', save_to_file_path)

                # figures out the CSV parameters (field sep, string delimiter, ...) hopefully
                dialect = csv.Sniffer().sniff(csvfile.read(4096))

                # Goes back to begining of file
                csvfile.seek(0)

                # skip top line with "GJK_Browscap_Version","GJK_Browscap_Version"
                csvfile.readline()

                # Determines Browscap file version ------------------------------

                line = next(csv.reader(StringIO(csvfile.readline()), dialect=dialect))
                # this gets the SECOND line of the file (the first was skipped)
                log.info('Getting browcap file version')
                local_version = line[0]

                log.info('Version of local Browscap file: {0}'.format(local_version))
        except FileNotFoundError:
            log.warning('No existing Browscap file for this path: {0}'.format(save_to_file_path))

        try:
            # --------------------- Getting latest version number from Browscap site -----------------------------------
            # url downloader set-up
            opener = urllib.request.build_opener()

            if self.proxy is not None:
                log.info('Setting up proxy server %s' % self.proxy)

                opener.add_handler(urllib.request.ProxyHandler({'http': self.proxy}))

                if self.additional_handlers is not None:
                    for handler in self.additional_handlers:
                        opener.add_handler(handler)
            opener.addheaders = [('User-agent', 'pybrowscap downloader')]

            urllib.request.install_opener(opener)

            # download the version number from the version URL
            response_version = opener.open(self.url_version, timeout=self.timeout)
            remote_version = bytes.decode(response_version.read())
            response_version.close()

            log.info('Latest version of browscap file from url [{0}] : {1}'.format(self.url_version, remote_version))

            # local version and latest version are the same --> No download
            if remote_version == local_version:
                log.info('Local file is up to date - no download')
                return

            # --------------------- Download file ----------------------------------------------------------------------
            log.warning('Downloading latest version of browscap file from %s', self.url_file)

            # download browscap file contents from file url
            response_file = opener.open(self.url_file, timeout=self.timeout)
            contents_file = response_file.read()
            response_file.close()

        except urllib.error.HTTPError:
            log.exception('Something went wrong while downloading browscap file')
            raise
        except urllib.error.URLError:
            log.exception('Something went wrong while processing urllib handlers')
            raise
        except ValueError:
            log.exception('Url to browscap file is probably invalid')
            raise

        # save file contents to the local far if we got thus far
        if save_to_file_path is not None and contents_file is not None:
            try:
                log.info('Saving latest version of browscap file to %s', save_to_file_path)
                with open(save_to_file_path, 'wb') as file:
                    file.write(contents_file)
            except IOError:
                log.exception('Error while saving latest version of browscap file')
                raise
        else:
            return contents_file


# ----------------------------------------------------------------------------------------------------------------------
class Browscap(object):
    """
    Browscap class represents abstraction on top of browscap data file.
    It contains all browscap data file data in python accessible form.

    """

    cm_browscap = None

    @classmethod
    def initBrowscap(cls, p_skip=False):
        if not p_skip:
            log.info("Downloading latest version of Browscap file ...")
            Downloader(g_browscapLatestVersionUrl, g_browscapUrl).get(g_browscapLocalFile)
            log.info("Processing Browscap file ...")
            cls.cm_browscap = load_browscap_file(g_browscapLocalFile)

    cache = {}

    def __init__(self, data_dict, regex_cache, browscap_file_path, type, version, release_date):
        """Constructor

        :param data_dict: dictionary of regex:line pairs
        :type data_dict: dict
        :param regex_cache: list of compiled regex patterns
        :type regex_cache: list
        :param browscap_file_path: path to the browscap file
        :type browscap_file_path: string
        :param type: type of browscap file csv, ini...
        :type type: int
        :param version: browscap file version
        :type version: int
        :param release_date: release date of browscap file
        :type release_date: datetime.datetime
        :returns: Browscap instance
        :rtype: pybrowscap.loader.Browscap

        """

        self.data = data_dict
        self.regex_cache = regex_cache
        self.browscap_file_path = browscap_file_path
        self.type = type
        self.version = version
        self.release_date = release_date
        self.loaded_at = datetime.now()
        self.reloaded_at = None

    def reload(self, browscap_file_path=None):
        """
        Reloads new data to this Browscap instance. This is useful
        mainly in apps that run in long living threads, like django projects.

        :param browscap_file_path: location of new browcap file on filesystem, or use old
        :type browscap_file_path: string or None
        :returns: None
        :raises: IOError

        """
        try:
            file_to_load = browscap_file_path or self.browscap_file_path
            log.info('Reloading browscap instance with file %s', file_to_load)

            reloaded_browscap = None
            if self.type == TYPE_CSV:
                reloaded_browscap = load_browscap_file(file_to_load)

            self.data = reloaded_browscap.data
            self.regex_cache = reloaded_browscap.regex_cache
            self.version = reloaded_browscap.version
            self.release_date = reloaded_browscap.release_date
            self.browscap_file_path = file_to_load
            self.cache = {}
            self.reloaded_at = datetime.now()
        except IOError:
            log.exception('Error while reloading Browscap instance with file %s', file_to_load)
            raise

    def search(self, user_agent_string):
        """Searching browscap data file for longest user_agent_string that matches the regex.

        :param user_agent_string: user agent to search in browscap file
        :type user_agent_string: string
        :returns: Browser instance or None
        :rtype: pybrowscap.Browser or None

        """
        log.info('Searching for user-agent: %s', user_agent_string)
        if user_agent_string in self.cache:
            log.debug('Cache-hit, searching skipped')
            return Browser(self.cache[user_agent_string])

        ua_regex_string = ''
        for ua_pattern in self.regex_cache:
            if ua_pattern.match(user_agent_string) and len(ua_pattern.pattern) > len(ua_regex_string):
                ua_regex_string = ua_pattern.pattern
        if ua_regex_string == '':
            log.info('No match found')
            return None
        else:
            log.info('Match found, returning Browser instance for: %s', ua_regex_string)
            self.cache[user_agent_string] = self.data[ua_regex_string]
            return Browser(self.data[ua_regex_string])