import os

from .vcs_base import find_executable, VcsClientBase


class SvnClient(VcsClientBase):

    _executable = None

    @staticmethod
    def is_repository(path):
        return os.path.isdir(os.path.join(path, '.svn'))

    def __init__(self, path):
        super(SvnClient, self).__init__('svn', path)

    def branch(self, _command):
        cmd = [SvnClient._executable, 'info']
        # only the line starting with 'URL:'
        return cmd

    def diff(self, command):
        cmd = [SvnClient._executable, 'diff']
        if command.context:
            cmd += ['--unified=%d' % command.context]
        return cmd

    def log(self, command):
        cmd = [SvnClient._executable, 'log', '--limit', '%d' % command.limit]
        return cmd

    def pull(self, _command):
        cmd = [SvnClient._executable, 'update']
        return cmd

    def push(self, _command):
        return None

    def remotes(self, _command):
        cmd = [SvnClient._executable, 'info']
        # only the line starting with 'URL:'
        return cmd

    def status(self, command):
        cmd = [SvnClient._executable, 'status']
        if command.quiet:
            cmd += ['--quiet']
        return cmd


if not SvnClient._executable:
    SvnClient._executable = find_executable('svn')
