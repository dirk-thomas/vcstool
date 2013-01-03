import os

from .vcs_base import find_executable, VcsClientBase


class BzrClient(VcsClientBase):

    type = 'bzr'
    _executable = None

    @staticmethod
    def is_repository(path):
        return os.path.isdir(os.path.join(path, '.bzr'))

    def __init__(self, path):
        super(BzrClient, self).__init__(path)

    def diff(self, _command):
        cmd = [BzrClient._executable, 'diff']
        return self._run_command(cmd)

    def log(self, command):
        if command.limit_untagged:
            # determine nearest tag
            cmd_tag = [BzrClient._executable, 'tags', '--sort=time']
            result_tag = self._run_command(cmd_tag)
            if result_tag['returncode']:
                return result_tag
            line = result_tag['output'].split('\n')[0]
            tag = line.split(' ')[0]
            if not tag:
                result_tag['output'] = 'Could not determine latest tag',
                result_tag['returncode'] = 1
                return result_tag
            # determine revision number of tag
            cmd_tag_rev = [BzrClient._executable, 'revno', '--rev', 'tag:%s' % tag]
            result_tag_rev = self._run_command(cmd_tag_rev)
            if result_tag_rev['returncode']:
                return result_tag_rev
            tag_rev = int(result_tag_rev['output'])
            # determine revision number of HEAD
            cmd_head_rev = [BzrClient._executable, 'revno']
            result_head_rev = self._run_command(cmd_head_rev)
            if result_head_rev['returncode']:
                return result_head_rev
            head_rev = int(result_head_rev['output'])
            # output log since nearest tag
            cmd_log = [BzrClient._executable, 'log', '--rev', 'revno:%d..' % (tag_rev + 1)]
            if tag_rev == head_rev:
                return {
                    'cmd': ' '.join(cmd_log),
                    'cwd': self.path,
                    'output': '',
                    'returncode': 0
                }
            result_log = self._run_command(cmd_log)
            return result_log
        cmd = [BzrClient._executable, 'log']
        if command.limit != 0:
            cmd += ['--limit', '%d' % command.limit]
        return self._run_command(cmd)

    def pull(self, _command):
        cmd = [BzrClient._executable, 'pull']
        return self._run_command(cmd)

    def push(self, _command):
        cmd = [BzrClient._executable, 'push']
        return self._run_command(cmd)

    def status(self, _command):
        cmd = [BzrClient._executable, 'status']
        return self._run_command(cmd)


if not BzrClient._executable:
    BzrClient._executable = find_executable('bzr')
    if not BzrClient._executable:
        raise ImportError('Could not find executable "bzr" for vcstool.clients.BzrClient')
