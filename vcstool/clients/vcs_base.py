import os
import socket
import subprocess
import time
import ssl
import base64
from urllib.error import HTTPError
from urllib.error import URLError
from urllib.request import Request
from urllib.request import urlopen


class VcsClientBase(object):

    type = None

    def __init__(self, path):
        ignore_certs = os.environ.get("VCS_IGNORE_SSL_CERTIFICATE", False)

        if ignore_certs:
            ssl._create_default_https_context = ssl._create_unverified_context

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


def _add_credentials_to_request(request, credentials_key):
    authentication_method = os.environ.get(f"VCS_{credentials_key}_AUTHENTICATION_METHOD", "Basic")
    token = os.environ.get(f"VCS_{credentials_key}_TOKEN", "")
    username = os.environ.get(f"VCS_{credentials_key}_USERNAME","")
    password = os.environ.get(f"VCS_{credentials_key}_PASSWORD", "")

    base64string = ""
    if authentication_method == "Basic" and (username or password):
        base64string = base64.b64encode(bytes(f"{username}:{password}", 'ascii')).decode('utf-8')
    elif authentication_method == "Token" or authentication_method == "Bearer":
        base64string = token

    request.add_header("Authorization", f"{authentication_method} {base64string}")


def load_url(url, retry=2, retry_period=1, timeout=10, credentials_key=None):
    request = Request(url)
    try:
        if credentials_key:
            _add_credentials_to_request(request, credentials_key)
        fh = urlopen(request, timeout=timeout)
    except HTTPError as e:
        if e.code == 503 and retry:
            time.sleep(retry_period)
            return load_url(
                url, retry=retry - 1, retry_period=retry_period,
                timeout=timeout)
        elif e.code == 401:
            if not credentials_key:
                e.msg += f". Credentials not provided. Add 'credentials_key' field in vcs file and " \
                    f"VCS_<KEY>_AUTHENTICATION_METHOD, VCS_<KEY>_USERNAME, VCS_<KEY>_PASSWORD, VCS_<KEY>_TOKEN " \
                    "environment variables to set up credentials."
            else:
                e.msg += f". Credentials invalid or missing. Set up authentication method with " \
                    f"VCS_{credentials_key}_AUTHENTICATION_METHOD ('Basic', 'Bearer' or 'Token') and " \
                    f"credentials with VCS_{credentials_key}_TOKEN or VCS_{credentials_key}_USERNAME " \
                    f"and VCS_{credentials_key}_PASSWORD environment variables."
        e.msg += ' (%s)' % url
        raise
    except URLError as e:
        if isinstance(e.reason, socket.timeout) and retry:
            time.sleep(retry_period)
            return load_url(
                url, retry=retry - 1, retry_period=retry_period,
                timeout=timeout)
        raise URLError(str(e) + ' (%s)' % url)
    return fh.read()


def test_url(url, retry=2, retry_period=1, timeout=10):
    request = Request(url)
    request.get_method = lambda: 'HEAD'

    try:
        response = urlopen(request)
    except HTTPError as e:
        if e.code == 503 and retry:
            time.sleep(retry_period)
            return test_url(
                url, retry=retry - 1, retry_period=retry_period,
                timeout=timeout)
        e.msg += ' (%s)' % url
        raise
    except URLError as e:
        if isinstance(e.reason, socket.timeout) and retry:
            time.sleep(retry_period)
            return test_url(
                url, retry=retry - 1, retry_period=retry_period,
                timeout=timeout)
        raise URLError(str(e) + ' (%s)' % url)
    return response
