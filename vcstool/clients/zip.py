import os
try:
    from cStringIO import StringIO as BytesIO
except ImportError:
    from io import BytesIO
try:
    from urllib.error import URLError
except ImportError:
    from urllib2 import URLError
import zipfile

from .vcs_base import load_url
from .vcs_base import test_url
from .vcs_base import VcsClientBase
from ..util import rmtree


class ZipClient(VcsClientBase):

    type = 'zip'

    @staticmethod
    def is_repository(path):
        return False

    def __init__(self, path):
        super(ZipClient, self).__init__(path)

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

        # download zipfile
        try:
            data = load_url(command.url, retry=command.retry)
        except URLError as e:
            return {
                'cmd': '',
                'cwd': self.path,
                'output':
                    "Could not fetch zipfile from '%s': %s" % (command.url, e),
                'returncode': 1
            }

        def create_path(path):
            if not os.path.exists(path):
                try:
                    os.makedirs(path)
                except os.error as e:
                    return {
                        'cmd': 'os.makedirs(%s)' % path,
                        'cwd': path,
                        'output':
                            "Could not create directory '%s': %s" % (path, e),
                        'returncode': 1
                    }
            return None

        # unpack zipfile into destination
        try:
            zip_file = zipfile.ZipFile(BytesIO(data), mode='r')
        except zipfile.BadZipfile as e:
            return {
                'cmd': 'ZipFile(%s)' % command.url,
                'cwd': self.path,
                'output':
                    "Could not read zipfile from '%s': %s" % (command.url, e),
                'returncode': 1
            }
        try:
            if not command.version:
                zip_file.extractall(self.path)
            else:
                prefix = str(command.version) + '/'
                for name in zip_file.namelist():
                    if name.startswith(prefix):
                        if not name[len(prefix):]:
                            continue
                        # remap members from version subfolder into destination
                        dst = os.path.join(self.path, name[len(prefix):])
                        if dst.endswith('/'):
                            # create directories
                            not_exist = create_path(dst)
                            if not_exist:
                                return not_exist
                        else:
                            with zip_file.open(name, mode='r') as src_handle:
                                with open(dst, 'wb') as dst_handle:
                                    dst_handle.write(src_handle.read())
        finally:
            zip_file.close()

        return {
            'cmd': '',
            'cwd': self.path,
            'output':
                "Downloaded zipfile from '%s' and unpacked it" % command.url,
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
                    "Failed to contact zip url '%s': %s" % (command.url, e),
                'returncode': 1
            }
        return {
            'cmd': 'http HEAD',
            'cwd': self.path,
            'output': "Zip url '%s' exists" % command.url,
            'returncode': None
        }
