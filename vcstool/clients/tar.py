import os
import shutil
import socket
try:
    from cStringIO import StringIO as BytesIO
except ImportError:
    from io import BytesIO
import tarfile
import time
try:
    from urllib.request import urlopen
    from urllib.error import HTTPError, URLError
except ImportError:
    from urllib2 import HTTPError, URLError, urlopen

from .vcs_base import VcsClientBase


class TarClient(VcsClientBase):

    type = 'tar'

    @staticmethod
    def is_repository(path):
        return False

    def __init__(self, path):
        super(TarClient, self).__init__(path)

    def import_(self, command):
        if not command.url or not command.version:
            if not command.url and not command.version:
                value_missing = "'url' and 'version'"
            elif not command.url:
                value_missing = "'url'"
            else:
                value_missing = "'version'"
            return {
                'cmd': '',
                'cwd': self.path,
                'output': 'Repository data lacks the %s value' % value_missing,
                'returncode': 1
            }

        # clear destination
        if os.path.exists(self.path):
            for filename in os.listdir(self.path):
                path = os.path.join(self.path, filename)
                try:
                    shutil.rmtree(path)
                except OSError:
                    os.remove(path)
        else:
            not_exist = self._create_path()
            if not_exist:
                return not_exist

        # download tarball
        try:
            data = _load_url(command.url)
        except URLError as e:
            return {
                'cmd': '',
                'cwd': self.path,
                'output': "Could not fetch tarball from '%s': %s" % (command.url, e),
                'returncode': 1
            }

        # unpack tarball into destination
        try:
            # raise all fatal errors
            tar = tarfile.open(mode='r', fileobj=BytesIO(data), errorlevel=1)
        except (tarfile.ReadError, IOError, OSError) as e:
            return {
                'cmd': '',
                'cwd': self.path,
                'output': "Failed to read tarball fetched from '%s': %s" % (command.url, e),
                'returncode': 1
            }

        # remap all members from version subfolder into destination
        def get_members(tar, prefix):
            for tar_info in tar.getmembers():
                if tar_info.name.startswith(prefix):
                    tar_info.name = tar_info.name[len(prefix):]
                    yield tar_info
        prefix = command.version + os.sep
        tar.extractall(self.path, get_members(tar, prefix))

        return {
            'cmd': '',
            'cwd': self.path,
            'output': "Downloaded tarball from '%s' and unpacked it" % command.url,
            'returncode': 0
        }


def _load_url(url, retry=2, retry_period=1, timeout=10):
    try:
        fh = urlopen(url, timeout=timeout)
    except HTTPError as e:
        if e.code == 503 and retry:
            time.sleep(retry_period)
            return _load_url(url, retry=retry - 1, retry_period=retry_period, timeout=timeout)
        e.msg += ' (%s)' % url
        raise
    except URLError as e:
        if isinstance(e.reason, socket.timeout) and retry:
            time.sleep(retry_period)
            return _load_url(url, retry=retry - 1, retry_period=retry_period, timeout=timeout)
        raise URLError(str(e) + ' (%s)' % url)
    return fh.read()
