import os
try:
    from cStringIO import StringIO as BytesIO
except ImportError:
    from io import BytesIO
import tarfile
try:
    from urllib.error import URLError
except ImportError:
    from urllib2 import URLError

from .vcs_base import load_url
from .vcs_base import test_url
from .vcs_base import VcsClientBase
from ..util import rmtree


class TarClient(VcsClientBase):

    type = 'tar'

    @staticmethod
    def is_repository(path):
        return False

    def __init__(self, path):
        super(TarClient, self).__init__(path)

    def import_(self, command):
        if not command.url:
            return {
                'cmd': '',
                'cwd': self.path,
                'output': "Repository data lacks the 'url' value",
                'returncode': 1
            }

        # clear destination
        if os.path.exists(self.path):
            for filename in os.listdir(self.path):
                path = os.path.join(self.path, filename)
                try:
                    rmtree(path)
                except OSError:
                    os.remove(path)
        else:
            not_exist = self._create_path()
            if not_exist:
                return not_exist

        # download tarball
        try:
            data = load_url(command.url, retry=command.retry)
        except URLError as e:
            return {
                'cmd': '',
                'cwd': self.path,
                'output':
                    "Could not fetch tarball from '%s': %s" % (command.url, e),
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
                'output':
                    "Failed to read tarball fetched from '%s': %s" %
                    (command.url, e),
                'returncode': 1
            }

        if not command.version:
            members = None
        else:
            # remap all members from version subfolder into destination
            def get_members(tar, prefix):
                for tar_info in tar.getmembers():
                    if tar_info.name.startswith(prefix):
                        tar_info.name = tar_info.name[len(prefix):]
                        yield tar_info
            prefix = str(command.version) + '/'
            members = get_members(tar, prefix)
        tar.extractall(self.path, members)

        return {
            'cmd': '',
            'cwd': self.path,
            'output':
                "Downloaded tarball from '%s' and unpacked it" % command.url,
            'returncode': 0
        }

    def validate(self, command):
        if not command.url:
            return {
                'cmd': '',
                'cwd': self.path,
                'output': "Repository data lacks the 'url' value",
                'returncode': 1
            }

        # test url
        try:
            test_url(command.url, retry=command.retry)
        except URLError as e:
            return {
                'cmd': '',
                'cwd': self.path,
                'output':
                    "Failed to contact tarball url '%s': %s" %
                    (command.url, e),
                'returncode': 1
            }
        return {
            'cmd': 'http HEAD url',
            'cwd': self.path,
            'output': "Tarball url '%s' exists" % command.url,
            'returncode': None
        }
