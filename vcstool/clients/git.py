import os
import subprocess

from .vcs_base import find_executable, VcsClientBase


class GitClient(VcsClientBase):

    _executable = None
    _config_color_is_auto = None

    @staticmethod
    def is_repository(path):
        return os.path.isdir(os.path.join(path, '.git'))

    def __init__(self, path):
        super(GitClient, self).__init__('git', path)

    def branch(self, _command):
        cmd = [GitClient._executable, 'branch']
        return cmd

    def diff(self, command):
        cmd = [GitClient._executable, 'diff']
        self._check_auto_color()
        if GitClient._config_color_is_auto:
            cmd = [cmd[0]] + ['-c', 'color.ui=always'] + cmd[1:]
        if command.context:
            cmd += ['--unified=%d' % command.context]
        return cmd

    def log(self, command):
        cmd = [GitClient._executable, 'log', '-%d' % command.limit]
        return cmd

    def pull(self, _command):
        cmd = [GitClient._executable, 'pull']
        return cmd

    def push(self, _command):
        cmd = [GitClient._executable, 'push']
        return cmd

    def remotes(self, _command):
        cmd = [GitClient._executable, 'remote', '-v']
        return cmd

    def status(self, command):
        cmd = [GitClient._executable, 'status']
        self._check_auto_color()
        if GitClient._config_color_is_auto:
            cmd = [cmd[0]] + ['-c', 'color.ui=always'] + cmd[1:]
        if command.quiet:
            cmd += ['--untracked-files=no']
        return cmd

    def _check_auto_color(self):
        # check if user uses colorization
        if GitClient._config_color_is_auto is None:
            output = subprocess.check_output([GitClient._executable, 'config', '--get', 'color.ui'], shell=False)
            GitClient._config_color_is_auto = output.strip() == 'auto'


if not GitClient._executable:
    GitClient._executable = find_executable('git')
