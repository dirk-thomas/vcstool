import os

from .vcs_base import VcsClientBase, which


class HgClient(VcsClientBase):

    type = 'hg'
    _executable = None
    _config_color = None

    @staticmethod
    def is_repository(path):
        return os.path.isdir(os.path.join(path, '.hg'))

    def __init__(self, path):
        super(HgClient, self).__init__(path)

    def branch(self, command):
        self._check_executable()
        cmd = [HgClient._executable, 'branches' if command.all else 'branch']
        self._check_color(cmd)
        return self._run_command(cmd)

    def custom(self, command):
        self._check_executable()
        cmd = [HgClient._executable] + command.args
        return self._run_command(cmd)

    def diff(self, command):
        self._check_executable()
        cmd = [HgClient._executable, 'diff']
        self._check_color(cmd)
        if command.context:
            cmd += ['--unified %d' % command.context]
        return self._run_command(cmd)

    def export(self, command):
        self._check_executable()
        result_url = self._get_url()
        if result_url['returncode']:
            return result_url
        url = result_url['output']

        cmd_id = [HgClient._executable, 'identify', '--id']
        result_id = self._run_command(cmd_id)
        if result_id['returncode']:
            result_id['output'] = 'Could not determine id: %s' % result_id['output']
            return result_id
        id_ = result_id['output']

        if not command.exact:
            cmd_branch = [HgClient._executable, 'identify', '--branch']
            result_branch = self._run_command(cmd_branch)
            if result_branch['returncode']:
                result_branch['output'] = 'Could not determine branch: %s' % result_branch['output']
                return result_branch
            branch = result_branch['output']

            cmd_branch_id = [HgClient._executable, 'identify', '-r', branch, '--id']
            result_branch_id = self._run_command(cmd_branch_id)
            if result_branch_id['returncode']:
                result_branch_id['output'] = 'Could not determine branch id: %s' % result_branch_id['output']
                return result_branch_id
            if result_branch_id['output'] == id_:
                id_ = branch
                cmd_branch = cmd_branch_id

        return {
            'cmd': '%s && %s' % (result_url['cmd'], ' '.join(cmd_id)),
            'cwd': self.path,
            'output': '\n'.join([url, id_]),
            'returncode': 0,
            'export_data': {'url': url, 'version': id_}
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

        self._check_executable()
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
        self._check_executable()
        if command.limit_tag:
            # check if specific tag exists
            cmd_log = [HgClient._executable, 'log', '--rev', 'tag(%s)' % command.limit_tag]
            result_log = self._run_command(cmd_log)
            if result_log['returncode']:
                return {
                    'cmd': '',
                    'cwd': self.path,
                    'output': "Repository lacks the tag '%s'" % command.limit_tag,
                    'returncode': 1
                }
            # output log since specific tag
            cmd = [HgClient._executable, 'log', '--rev', 'sort(tag(%s)::, -rev) and not tag (%s)' % (command.limit_tag, command.limit_tag)]
        elif command.limit_untagged:
            # determine distance to nearest tag
            cmd_log = [HgClient._executable, 'log', '--rev', '.', '--template', '{latesttagdistance}']
            result_log = self._run_command(cmd_log)
            if result_log['returncode']:
                return result_log
            # output log since nearest tag
            cmd = [HgClient._executable, 'log', '--limit', result_log['output'], '-b', '.']
        else:
            cmd = [HgClient._executable, 'log']
            if command.limit != 0:
                cmd += ['--limit', '%d' % command.limit]
        self._check_color(cmd)
        return self._run_command(cmd)

    def pull(self, _command):
        self._check_executable()
        cmd = [HgClient._executable, 'pull', '--update']
        self._check_color(cmd)
        return self._run_command(cmd)

    def push(self, _command):
        self._check_executable()
        cmd = [HgClient._executable, 'push']
        return self._run_command(cmd)

    def remotes(self, _command):
        self._check_executable()
        cmd = [HgClient._executable, 'paths']
        return self._run_command(cmd)

    def status(self, command):
        self._check_executable()
        cmd = [HgClient._executable, 'status']
        self._check_color(cmd)
        if command.quiet:
            cmd += ['--untracked-files=no']
        return self._run_command(cmd)

    def _check_color(self, cmd):
        # check if user uses colorization
        if HgClient._config_color is None:
            HgClient._config_color = False
            # check if config extension is available
            _cmd = [HgClient._executable, 'config', '--help']
            result = self._run_command(_cmd)
            if result['returncode'] != 0:
                return
            # check if color extension is available and not disabled
            _cmd = [HgClient._executable, 'config', 'extensions.color']
            result = self._run_command(_cmd)
            if result['returncode'] != 0 or result['output'].startswith('!'):
                return
            # check if color mode is not off
            _cmd = [HgClient._executable, 'config', 'color.mode']
            result = self._run_command(_cmd)
            if result['returncode'] != 0 or result['output'] == 'off':
                return
            HgClient._config_color = True

        # inject arguments to force colorization
        if HgClient._config_color:
            cmd[1:1] = '--color', 'always'

    def _check_executable(self):
        assert HgClient._executable is not None, "Could not find 'hg' executable"


if not HgClient._executable:
    HgClient._executable = which('hg')
