import errno
import functools
import glob
import logging
import netrc
import os
import socket
import subprocess
import time
try:
    from urllib.request import Request
    from urllib.request import urlopen
    from urllib.request import HTTPPasswordMgrWithDefaultRealm
    from urllib.request import HTTPBasicAuthHandler
    from urllib.request import build_opener
    from urllib.parse import urlparse
    from urllib.error import HTTPError
    from urllib.error import URLError
except ImportError:
    from urllib2 import HTTPError
    from urllib2 import Request
    from urllib2 import URLError
    from urllib2 import urlopen
    from urllib2 import HTTPPasswordMgrWithDefaultRealm
    from urllib2 import HTTPBasicAuthHandler
    from urllib2 import build_opener
    from urlparse import urlparse

try:
    from shutil import which  # noqa
except ImportError:
    from vcstool.compat.shutil import which  # noqa

import appdirs

_AUTHENTICATION_CONFIGURATION_FILE = "auth.conf"
_AUTHENTICATION_CONFIGURATION_PARTS_DIR = "auth.conf.d"
_APPDIRS_PROJECT_NAME = 'vcstool'

logger = logging.getLogger(__name__)


class VcsClientBase(object):

    type = None

    def __init__(self, path):
        self.path = path

    def __getattribute__(self, name):
        if name == 'import':
            try:
                return self.import_
            except AttributeError:
                pass
        return super(VcsClientBase, self).__getattribute__(name)

    def _not_applicable(self, command, message=None):
        return {
            'cmd': '%s.%s(%s)' % (
                self.__class__.type, 'push', command.__class__.command),
            'output': "Command '%s' not applicable for client '%s'%s" % (
                command.__class__.command, self.__class__.type,
                ': ' + message if message else ''),
            'returncode': NotImplemented
        }

    def _run_command(self, cmd, env=None, retry=0):
        for i in range(retry + 1):
            result = run_command(cmd, os.path.abspath(self.path), env=env)
            if not result['returncode']:
                # return successful result
                break
            if i >= retry:
                # return the failure after retries
                break
            # increasing sleep before each retry
            time.sleep(i + 1)
        return result

    def _create_path(self):
        if not os.path.exists(self.path):
            try:
                os.makedirs(self.path)
            except os.error as e:
                return {
                    'cmd': 'os.makedirs(%s)' % self.path,
                    'cwd': self.path,
                    'output':
                        "Could not create directory '%s': %s" % (self.path, e),
                    'returncode': 1
                }
        return None


def run_command(cmd, cwd, env=None):
    if not os.path.exists(cwd):
        cwd = None
    result = {'cmd': ' '.join(cmd), 'cwd': cwd}
    try:
        proc = subprocess.Popen(
            cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            env=env)
        output, _ = proc.communicate()
        result['output'] = output.rstrip().decode('utf8')
        result['returncode'] = proc.returncode
    except subprocess.CalledProcessError as e:
        result['output'] = e.output.decode('utf8')
        result['returncode'] = e.returncode
    return result


def load_url(url, retry=2, retry_period=1, timeout=10):
    fh = None
    try:
        fh = _retryable_urlopen(url, timeout=timeout)
    except HTTPError as e:
        if e.code in (401, 404):
            # Try again, but with authentication
            fh = _authenticated_urlopen(url, timeout=timeout)
        if fh is None:
            e.msg += ' (%s)' % url
            raise
    except URLError as e:
        raise URLError(str(e) + ' (%s)' % url)

    return fh.read()


def test_url(url, retry=2, retry_period=1, timeout=10):
    request = Request(url)
    request.get_method = lambda: 'HEAD'

    try:
        response = _retryable_urlopen(request)
    except HTTPError as e:
        e.msg += ' (%s)' % url
        raise
    except URLError as e:
        raise URLError(str(e) + ' (%s)' % url)
    return response


def _urlopen_retry(f):
    @functools.wraps(f)
    def _retryable_function(url, retry=2, retry_period=1, timeout=10):
        retry += 1

        while True:
            try:
                retry -= 1
                return f(url, timeout=timeout)
            except HTTPError as e:
                if e.code != 503 or retry <= 0:
                    raise
            except URLError as e:
                if not isinstance(e.reason, socket.timeout) or retry <= 0:
                    raise

            if retry > 0:
                time.sleep(retry_period)
            else:
                break

    return _retryable_function


@_urlopen_retry
def _retryable_urlopen(url, timeout=10):
    return urlopen(url, timeout=timeout)


@_urlopen_retry
def _authenticated_urlopen(uri, timeout=10):
    machine = urlparse(uri).netloc
    if not machine:
        return None

    credentials = _credentials_for_machine(machine)
    if credentials is None:
        return None

    (username, account, password) = credentials

    # If we have both a username and a password, use basic auth
    if username and password:
        password_manager = HTTPPasswordMgrWithDefaultRealm()
        password_manager.add_password(None, machine, username, password)
        auth_handler = HTTPBasicAuthHandler(password_manager)
        opener = build_opener(auth_handler)
        return opener.open(uri, timeout=timeout)

    # If we have only a password, use token auth
    elif password:
        request = Request(uri)
        request.add_header('PRIVATE-TOKEN', password)
        return urlopen(request, timeout=timeout)

    return None


def _credentials_for_machine(machine):
    # First check the default .netrc file, if any-- it takes precedence over
    # everything else
    credentials = _credentials_for_machine_in_file(None, machine)
    if credentials:
        return credentials

    # If that file either didn't exist or didn't match for the machine,
    # check the user auth directory for vcstool
    credentials = _credentials_for_machine_in_dir(
        appdirs.user_config_dir(_APPDIRS_PROJECT_NAME), machine)
    if credentials:
        return credentials

    # Finally, check the system-wide auth directory for vcstool
    return _credentials_for_machine_in_dir(
        appdirs.site_config_dir(_APPDIRS_PROJECT_NAME), machine)


def _credentials_for_machine_in_dir(directory, machine):
    # The idea here is similar to how Debian handles authenticated apt repos:
    # https://manpages.debian.org/testing/apt/apt_auth.conf.5.en.html

    # Check the auth.conf file first
    auth_file_path = os.path.join(
        directory, _AUTHENTICATION_CONFIGURATION_FILE)
    credentials = _credentials_for_machine_in_file(auth_file_path, machine)
    if credentials:
        return credentials

    # If that file either didn't exist or didn't match for the machine, check
    # the .conf files in the configuration parts dir
    configuration_parts_dir = os.path.join(
        directory, _AUTHENTICATION_CONFIGURATION_PARTS_DIR)
    auth_files = glob.glob(os.path.join(configuration_parts_dir, '*.conf'))
    for auth_file in sorted(auth_files):
        auth_file_path = os.path.join(configuration_parts_dir, auth_file)
        credentials = _credentials_for_machine_in_file(auth_file_path, machine)
        if credentials:
            return credentials

    # Nothing matched
    return None


def _credentials_for_machine_in_file(filename, machine):
    credentials = None
    try:
        credentials = netrc.netrc(file=filename).authenticators(machine)
    except EnvironmentError as e:
        # Don't error just because the file didn't exist or we didn't have
        # permission to access it. Catching this situation this way to be
        # compatible with python 2 and 3.
        if e.errno not in (errno.ENOENT, errno.EACCES):
            raise
    except netrc.NetrcParseError:
        # If this file had issues, don't error out so we can try fallbacks
        pass

    return credentials
