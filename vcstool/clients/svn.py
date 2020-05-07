import os
from xml.etree.ElementTree import fromstring

from .vcs_base import VcsClientBase, which


class SvnClient(VcsClientBase):

    type = 'svn'
    _executable = None

    @staticmethod
    def is_repository(path):
        return os.path.isdir(os.path.join(path, '.svn'))

    def __init__(self, path):
        super(SvnClient, self).__init__(path)

    def branch(self, command):
        if command.all:
            return self._not_applicable(
                command,
                message='at least with the option to list all branches')

        self._check_executable()
        cmd_info = [SvnClient._executable, 'info', '--xml']
        result_info = self._run_command(cmd_info)
        if result_info['returncode']:
            result_info['output'] = \
                'Could not determine url: ' + result_info['output']
            return result_info
        info = result_info['output']

        try:
            root = fromstring(info)
            entry = root.find('entry')
            url = entry.findtext('url')
            repository = entry.find('repository')
            root_url = repository.findtext('root')
        except Exception as e:
            return {
                'cmd': '',
                'cwd': self.path,
                'output': 'Could not determine url from xml: %s' % e,
                'returncode': 1
            }

        if not url.startswith(root_url):
            return {
                'cmd': '',
                'cwd': self.path,
                'output':
                    "Could not determine url suffix. The root url '%s' is not "
                    "a prefix of the url '%s'" % (root_url, url),
                'returncode': 1
            }

        return {
            'cmd': ' '.join(cmd_info),
            'cwd': self.path,
            'output': url[len(root_url):],
            'returncode': 0,
        }

    def custom(self, command):
        self._check_executable()
        cmd = [SvnClient._executable] + command.args
        return self._run_command(cmd)

    def diff(self, command):
        self._check_executable()
        cmd = [SvnClient._executable, 'diff']
        if command.context:
            cmd += ['--unified=%d' % command.context]
        return self._run_command(cmd)

    def export(self, command):
        self._check_executable()
        cmd_info = [SvnClient._executable, 'info', '--xml']
        result_info = self._run_command(cmd_info)
        if result_info['returncode']:
            result_info['output'] = \
                'Could not determine url: ' + result_info['output']
            return result_info
        info = result_info['output']

        try:
            root = fromstring(info)
            entry = root.find('entry')
            url = entry.findtext('url')
            revision = entry.get('revision')
        except Exception as e:
            return {
                'cmd': '',
                'cwd': self.path,
                'output': 'Could not determine url from xml: %s' % e,
                'returncode': 1
            }

        export_data = {'url': url}
        if command.exact:
            export_data['version'] = revision
        return {
            'cmd': ' '.join(cmd_info),
            'cwd': self.path,
            'output': url,
            'returncode': 0,
            'export_data': export_data
        }

    def import_(self, command):
        if not command.url:
            return {
                'cmd': '',
                'cwd': self.path,
                'output': "Repository data lacks the 'url' value",
                'returncode': 1
            }

        not_exist = self._create_path()
        if not_exist:
            return not_exist

        self._check_executable()

        url = command.url
        if command.version:
            url += '@%s' % command.version

        cmd_checkout = [
            SvnClient._executable, '--non-interactive', 'checkout', url, '.']
        result_checkout = self._run_command(cmd_checkout, retry=command.retry)
        if result_checkout['returncode']:
            result_checkout['output'] = \
                "Could not checkout repository '%s': %s" % \
                (command.url, result_checkout['output'])
            return result_checkout

        return {
            'cmd': ' '.join(cmd_checkout),
            'cwd': self.path,
            'output': result_checkout['output'],
            'returncode': 0
        }

    def log(self, command):
        if command.limit_tag:
            return {
                'cmd': '',
                'cwd': self.path,
                'output': 'SvnClient can not determine log since tag',
                'returncode': NotImplemented
            }
        if command.limit_untagged:
            return {
                'cmd': '',
                'cwd': self.path,
                'output': 'SvnClient can not determine latest tag',
                'returncode': NotImplemented
            }
        self._check_executable()
        cmd = [SvnClient._executable, 'log']
        if command.limit != 0:
            cmd += ['--limit', '%d' % command.limit]
        return self._run_command(cmd)

    def pull(self, _command):
        self._check_executable()
        cmd = [SvnClient._executable, '--non-interactive', 'update']
        return self._run_command(cmd)

    def push(self, command):
        self._check_executable()
        return self._not_applicable(command)

    def remotes(self, _command):
        self._check_executable()
        cmd_info = [SvnClient._executable, 'info', '--xml']
        result_info = self._run_command(cmd_info)
        if result_info['returncode']:
            result_info['output'] = \
                'Could not determine url: ' + result_info['output']
            return result_info
        info = result_info['output']

        try:
            root = fromstring(info)
            entry = root.find('entry')
            url = entry.findtext('url')
        except Exception as e:
            return {
                'cmd': '',
                'cwd': self.path,
                'output': 'Could not determine url from xml: %s' % e,
                'returncode': 1
            }

        return {
            'cmd': ' '.join(cmd_info),
            'cwd': self.path,
            'output': url,
            'returncode': 0,
        }

    def status(self, command):
        self._check_executable()
        cmd = [SvnClient._executable, 'status']
        if command.quiet:
            cmd += ['--quiet']
        return self._run_command(cmd)

    def validate(self, command):
        if not command.url:
            return {
                'cmd': '',
                'cwd': self.path,
                'output': "Repository data lacks the 'url' value",
                'returncode': 1
            }

        self._check_executable()

        cmd_info_repo = [SvnClient._executable, 'info', command.url]
        result_info_repo = self._run_command(
            cmd_info_repo,
            retry=command.retry)
        if result_info_repo['returncode']:
            result_info_repo['output'] = \
                "Failed to contact remote repository '%s': %s" % \
                (command.url, result_info_repo['output'])
            return result_info_repo

        if command.version:
            cmd_info_ver = [
                SvnClient._executable, 'info',
                command.url + '@' + command.version]
            result_info_ver = self._run_command(
                cmd_info_ver,
                retry=command.retry)

            if result_info_ver['returncode']:
                result_info_ver['output'] = \
                    'Specified version not found on remote repository' + \
                    "'%s@%s' : %s" % \
                    (command.url, command.version, result_info_ver['output'])
                return result_info_ver

            cmd = result_info_ver['cmd']
            output = "Found svn repository '%s' with revision '%s'" % \
                (command.url, command.version)
        else:
            cmd = result_info_repo['cmd']
            output = "Found svn repository '%s' with default branch" % \
                command.url

        return {
            'cmd': cmd,
            'cwd': self.path,
            'output': output,
            'returncode': None
        }

    def _check_executable(self):
        assert SvnClient._executable is not None, \
            "Could not find 'svn' executable"


if not SvnClient._executable:
    SvnClient._executable = which('svn')
