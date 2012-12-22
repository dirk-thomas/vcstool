import os

from .vcs_base import find_executable, VcsClientBase


class HgClient(VcsClientBase):

    _executable = None

    @staticmethod
    def is_repository(path):
        return os.path.isdir(os.path.join(path, '.hg'))

    def __init__(self, path):
        super(HgClient, self).__init__('hg', path)

    def branch(self, _command):
        cmd = [HgClient._executable, 'branch']
        return cmd

    def diff(self, command):
        cmd = [HgClient._executable, 'diff']
        if command.context:
            cmd += ['--unified %d' % command.context]
        return cmd

    def log(self, command):
        cmd = [HgClient._executable, 'log', '--limit', '%d' % command.limit]
        return cmd

    def pull(self, _command):
        cmd = [HgClient._executable, 'pull', '--update']
        return cmd

    def push(self, _command):
        cmd = [HgClient._executable, 'push']
        return cmd

    def remotes(self, _command):
        cmd = [HgClient._executable, 'paths']
        return cmd

    def status(self, command):
        cmd = [HgClient._executable, 'status']
        if command.quiet:
            cmd += ['--untracked-files=no']
        return cmd


if not HgClient._executable:
    HgClient._executable = find_executable('hg')
