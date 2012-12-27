import os

from .vcs_base import find_executable, VcsClientBase


class HgClient(VcsClientBase):

    type = 'hg'
    _executable = None

    @staticmethod
    def is_repository(path):
        return os.path.isdir(os.path.join(path, '.hg'))

    def __init__(self, path):
        super(HgClient, self).__init__(path)

    def branch(self, _command):
        cmd = [HgClient._executable, 'branch']
        return self._run_command(cmd)

    def diff(self, command):
        cmd = [HgClient._executable, 'diff']
        if command.context:
            cmd += ['--unified %d' % command.context]
        return self._run_command(cmd)

    def export(self, _command):
        result_url = self._get_url()
        if result_url['returncode']:
            return result_url
        url = result_url['output']

        cmd_branch = [HgClient._executable, 'branch']
        result_branch = self._run_command(cmd_branch)
        if result_branch['returncode']:
            result_branch['output'] = 'Could not determine branch: %s' % result_branch['output']
            return result_branch
        branch = result_branch['output']

        cmd = cmd_url + ['&&'] + cmd_branch
        return {
            'cmd': ' '.join(cmd),
            'cwd': self.path,
            'output': '\n'.join([url, branch]),
            'returncode': 0,
            'export_data': {'url': url, 'version': branch}
        }

    def _get_url(self):
        cmd_url = [HgClient._executable, 'paths', 'default']
        result_url = self._run_command(cmd_url)
        if result_url['returncode']:
            result_url['output'] = 'Could not determine url: %s' % result_url['output']
            return result_url
        return result_url

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

        if HgClient.is_repository(self.path):
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
            cmd_pull = [HgClient._executable, 'pull', '--update']
            result_pull = self._run_command(cmd_pull)
            if result_pull['returncode']:
                return result_pull
            cmd = result_pull['cmd']
            output = result_pull['output']

        else:
            cmd_clone = [HgClient._executable, 'clone', command.url, '.']
            result_clone = self._run_command(cmd_clone)
            if result_clone['returncode']:
                result_clone['output'] = "Could not clone repository '%s': %s" % (command.url, result_clone['output'])
                return result_clone
            cmd = result_clone['cmd']
            output = result_clone['output']

        if command.version:
            cmd_checkout = [HgClient._executable, 'checkout', command.version]
            result_checkout = self._run_command(cmd_checkout)
            if result_checkout['returncode']:
                result_checkout['output'] = "Could not checkout '%s': %s" % (command.version, result_clone['output'])
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
        cmd = [HgClient._executable, 'log', '--limit', '%d' % command.limit]
        return self._run_command(cmd)

    def pull(self, _command):
        cmd = [HgClient._executable, 'pull', '--update']
        return self._run_command(cmd)

    def push(self, _command):
        cmd = [HgClient._executable, 'push']
        return cmd

    def remotes(self, _command):
        cmd = [HgClient._executable, 'paths']
        return self._run_command(cmd)

    def status(self, command):
        cmd = [HgClient._executable, 'status']
        if command.quiet:
            cmd += ['--untracked-files=no']
        return self._run_command(cmd)


if not HgClient._executable:
    HgClient._executable = find_executable('hg')
