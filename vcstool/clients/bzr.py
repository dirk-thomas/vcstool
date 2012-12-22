import os

from .vcs_base import find_executable, VcsClientBase


class BzrClient(VcsClientBase):

    _executable = None

    @staticmethod
    def is_repository(path):
        return os.path.isdir(os.path.join(path, '.bzr'))

    def __init__(self, path):
        super(BzrClient, self).__init__('bzr', path)

    def branch(self, _command):
        return None

    def diff(self, _command):
        cmd = [BzrClient._executable, 'diff']
        return cmd

    def log(self, command):
        cmd = [BzrClient._executable, 'log', '--limit', '%d' % command.limit]
        return cmd

    def pull(self, _command):
        cmd = [BzrClient._executable, 'pull']
        return cmd

    def push(self, _command):
        cmd = [BzrClient._executable, 'push']
        return cmd

    def remotes(self, _command):
        return None

    def status(self, _command):
        cmd = [BzrClient._executable, 'status']
        return cmd


if not BzrClient._executable:
    BzrClient._executable = find_executable('bbzr')
    if not BzrClient._executable:
        raise ImportError('Could not find executable "bzr" for vcstool.clients.BzrClient')
