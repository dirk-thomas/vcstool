import copy
import os

from .vcs_base import find_executable, VcsClientBase


class GitClient(VcsClientBase):

    type = 'git'
    _executable = None
    _config_color_is_auto = None

    @staticmethod
    def is_repository(path):
        return os.path.isdir(os.path.join(path, '.git'))

    def __init__(self, path):
        super(GitClient, self).__init__(path)

    def branch(self, _command):
        cmd = [GitClient._executable, 'branch']
        return self._run_command(cmd)

    def diff(self, command):
        cmd = [GitClient._executable, 'diff']
        self._check_auto_color()
        if GitClient._config_color_is_auto:
            cmd = [cmd[0]] + ['-c', 'color.ui=always'] + cmd[1:]
        if command.context:
            cmd += ['--unified=%d' % command.context]
        return self._run_command(cmd)

    def export(self, command):
        result_url = self._get_url()
        if result_url['returncode']:
            return result_url
        url = result_url['output']

        cmd_ref = [GitClient._executable, 'rev-parse', 'HEAD']
        result_ref = self._run_command(cmd_ref)
        if result_ref['returncode']:
            result_ref['output'] = 'Could not determine ref: %s' % result_ref['output']
            return result_ref
        ref = result_ref['output']

        if not command.exact:
            cmd_abbrev_ref = [GitClient._executable, 'rev-parse', '--abbrev-ref', 'HEAD']
            result_abbrev_ref = self._run_command(cmd_abbrev_ref)
            if result_abbrev_ref['returncode']:
                result_abbrev_ref['output'] = 'Could not determine abbrev-ref: %s' % result_abbrev_ref['output']
                return result_abbrev_ref
            if result_abbrev_ref['output'] != 'HEAD':
                ref = result_abbrev_ref['output']
                cmd_ref = cmd_abbrev_ref

        return {
            'cmd': '%s && %s' % (result_url['cmd'], ' '.join(cmd_ref)),
            'cwd': self.path,
            'output': '\n'.join([url, ref]),
            'returncode': 0,
            'export_data': {'url': url, 'version': ref}
        }

    def _get_url(self):
        cmd_remote = [GitClient._executable, 'remote', 'show']
        result_remote = self._run_command(cmd_remote)
        if result_remote['returncode']:
            result_remote['output'] = 'Could not determine remote: %s' % result_remote['output']
            return result_remote
        remote = result_remote['output']

        cmd_url_tpl = [GitClient._executable, 'config', '--get', 'remote.%s.url']
        cmd_url = copy.copy(cmd_url_tpl)
        cmd_url[-1] = cmd_url[-1] % remote
        result_url = self._run_command(cmd_url)
        if result_url['returncode']:
            result_url['output'] = 'Could not determine remote url: %s' % result_url['output']
            return result_url
        url = result_url['output']

        cmd = copy.copy(cmd_url_tpl)
        cmd[-1] = cmd[-1] % ('`%s`' % ' '.join(cmd_remote))
        return {
            'cmd': ' '.join(cmd),
            'cwd': self.path,
            'output': url,
            'returncode': 0
        }

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

        not_exist = self._create_path()
        if not_exist:
            return not_exist

        if GitClient.is_repository(self.path):
            # verify that existing repository is the same
            result_url = self._get_url()
            if result_url['returncode']:
                return result_url
            url = result_url['output']
            if url != command.url:
                return {
                    'cmd': '',
                    'cwd': self.path,
                    'output': 'Path already exists and contains a different repository',
                    'returncode': 1
                }
            # pull updates for existing repo
            cmd_pull = [GitClient._executable, 'pull']
            result_pull = self._run_command(cmd_pull)
            if result_pull['returncode']:
                return result_pull
            cmd = result_pull['cmd']
            output = result_pull['output']

        else:
            cmd_clone = [GitClient._executable, 'clone', command.url, '.']
            result_clone = self._run_command(cmd_clone)
            if result_clone['returncode']:
                result_clone['output'] = "Could not clone repository '%s': %s" % (command.url, result_clone['output'])
                return result_clone
            cmd = result_clone['cmd']
            output = result_clone['output']

        cmd_checkout = [GitClient._executable, 'checkout', command.version]
        result_checkout = self._run_command(cmd_checkout)
        if result_checkout['returncode']:
            result_checkout['output'] = "Could not checkout ref '%s': %s" % (command.version, result_checkout['output'])
            return result_checkout
        cmd += ' && ' + ' '.join(cmd_checkout)
        output = '\n'.join([output, result_checkout['output']])

        return {
            'cmd': cmd,
            'cwd': self.path,
            'output': output,
            'returncode': 0
        }

    def log(self, command):
        if not command.limit_untagged:
            cmd = [GitClient._executable, 'log']
            if command.limit != 0:
                cmd += ['-%d' % command.limit]
        else:
            # determine nearest tag
            cmd_tag = [GitClient._executable, 'describe', '--abbrev=0', '--tags']
            result_tag = self._run_command(cmd_tag)
            if result_tag['returncode']:
                return result_tag
            # output log since nearest tag
            cmd = [GitClient._executable, 'log', '%s..' % result_tag['output']]
        return self._run_command(cmd)

    def pull(self, _command):
        cmd = [GitClient._executable, 'pull']
        return self._run_command(cmd)

    def push(self, _command):
        cmd = [GitClient._executable, 'push']
        return self._run_command(cmd)

    def remotes(self, _command):
        cmd = [GitClient._executable, 'remote', '-v']
        return self._run_command(cmd)

    def status(self, command):
        cmd = [GitClient._executable, 'status']
        self._check_auto_color()
        if GitClient._config_color_is_auto:
            cmd = [cmd[0]] + ['-c', 'color.ui=always'] + cmd[1:]
        if command.quiet:
            cmd += ['--untracked-files=no']
        return self._run_command(cmd)

    def _check_auto_color(self):
        # check if user uses colorization
        if GitClient._config_color_is_auto is None:
            cmd = [GitClient._executable, 'config', '--get', 'color.ui']
            result = self._run_command(cmd)
            GitClient._config_color_is_auto = (result['output'] == 'auto')


if not GitClient._executable:
    GitClient._executable = find_executable('git')
