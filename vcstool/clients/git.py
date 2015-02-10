import copy
import os
import re

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

    def custom(self, command):
        cmd = [GitClient._executable] + command.args
        return self._run_command(cmd)

    def diff(self, command):
        cmd = [GitClient._executable, 'diff']
        self._check_color(cmd)
        if command.context:
            cmd += ['--unified=%d' % command.context]
        return self._run_command(cmd)

    def export(self, command):

        # Get the remote and remote reference
        result_remote = self._get_remote_ref(command.exact)
        if result_remote['returncode']:
            return result_remote

        remote = result_remote['output'][0]
        ref = result_remote['output'][1]

        # Get the url for this remote
        result_url = self._get_url(remote)
        if result_url['returncode']:
            return result_url

        url = result_url['output'][0]

        return {
            'cmd': '%s && %s' % (result_remote['cmd'], result_url['cmd']),
            'cwd': self.path,
            'output': '\n'.join([url, ref]),
            'returncode': 0,
            'export_data': {'url': url, 'version': ref}
        }

    def _get_remote_ref(self, exact=False):
        """Get the remote name and remote reference for the current checkout.

        param: exact: Get the SHA1 even if there is a remote branch or tag name
        """

        cmd_branch_vv = [GitClient._executable, 'branch', '-vv', '--abbrev=0', '--color=never']
        result_branch_vv = self._run_command(cmd_branch_vv)
        if result_branch_vv['returncode']:
            result_branch_vv['output'] = 'Could not determine local branches: %s' % result_branch_vv['output']
            return result_branch_vv
        branches = result_branch_vv['output']

        # regex patterns for branches and detached snapshots
        branch_pattern = '^\*\s+(.+?)\s+([0-9a-fA-F]+)\s\[(.+?)/(.+)\]'
        detached_pattern = '^\*\s+\(detached from (.+)\)\s+([0-9a-fA-F]+)'
        remote_tags_pattern = '^([0-9a-fA-F]+)\s+refs\/tags\/(.+)'

        sed_cmd = lambda p,r: "sed -re 's@%s@%s@p;d'" % (p, r)

        branch_re = re.compile(branch_pattern, re.MULTILINE)
        detached_re = re.compile(detached_pattern, re.MULTILINE)
        remote_tags_re = re.compile(remote_tags_pattern, re.MULTILINE)

        # Check for branch checkout
        for (local_branch_, snapshot_, remote_, remote_branch_) in branch_re.findall(branches):
            ref = snapshot_ if exact else remote_branch_
            return {
                'cmd': ' '.join([result_branch_vv['cmd'], '|', sed_cmd(branch_pattern,'\\3 \\4')]),
                'output': [remote_, ref],
                'returncode': 0
            }

        # Check for detached checkout
        for (detached_name_, snapshot_) in detached_re.findall(branches):

            # Get the list of remotes
            cmd_remote = [GitClient._executable, 'remote', 'show']
            result_remote = self._run_command(cmd_remote)
            if result_remote['returncode']:
                result_remote['output'] = 'Could not determine remotes when looking for remote snapshot: %s' % result_remote['output']
                return result_remote
            remotes = result_remote['output']

            # Find ANY remote with a tag referencing this snapshot
            for remote_ in remotes.splitlines():
                cmd_remote_tags = [GitClient._executable, 'ls-remote', '--tags', remote_]
                result_remote_tags = self._run_command(cmd_remote_tags)
                if result_remote_tags['returncode']:
                    result_remote_tags['output'] = 'Could not determine remote tags when looking for remote snapshot: %s' % result_remote_tags['output']
                    return result_remote_tags

                remote_tags = result_remote_tags['output']

                for (remote_snapshot_, remote_tag_) in remote_tags_re.findall(remote_tags):
                    if remote_snapshot_ == snapshot_:
                        ref = remote_snapshot_ if exact else remote_tag_
                        return {
                            'cmd': result_remote_tags['cmd'],
                            'output': [remote_, ref],
                            'returncode': 0
                        }

            # Find ANY remote with this snapshot
            for remote_ in remotes.splitlines():
                cmd_rev_list = [GitClient._executable, 'rev-list', '--remotes=%s' % (remote_)]
                result_rev_list = self._run_command(cmd_rev_list)
                if result_rev_list['returncode']:
                    result_rev_list['output'] = 'Could not determine remote tags when looking for remote snapshot: %s' % result_rev_list['output']
                    return result_rev_list

                rev_list = result_rev_list['output']

                for rev in rev_list.splitlines():
                    if rev == snapshot_:
                        return {
                            'cmd': ' '.join([cmd_rev_list['cmd'],'|','grep',snapshot_]),
                            'output': [remote_, snapshot_],
                            'returncode': 0
                        }

        return {
            'cmd': result_branch_vv['cmd'],
            'output': 'Could not determine remote for current checkout: \n\n'+result_branch_vv['output'],
            'returncode': -1,
        }

    def _get_url(self, remote=None):

        # get the remote and remote reference
        if remote is None:
            result_get_remote = self._get_remote_ref()
            if result_get_remote['returncode'] != 0:
                result_get_remote['output'] = 'Could not determine remote: %s' % result_get_remote['output']
                return result_get_remote

            remote = result_get_remote['output'][0]

        cmd_url = [GitClient._executable, 'config', '--get', 'remote.%s.url' % remote]
        result_url = self._run_command(cmd_url)
        if result_url['returncode']:
            result_url['output'] = 'Could not determine remote url: %s' % result_url['output']
            return result_url
        url = result_url['output']

        return {
            'cmd': result_url['cmd'],
            'cwd': self.path,
            'output': [url, remote],
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
            url = result_url['output'][0]
            remote = result_url['output'][1]
            if url != command.url:
                return {
                    'cmd': '',
                    'cwd': self.path,
                    'output': 'Path already exists and contains a different repository',
                    'returncode': 1
                }
            # pull updates for existing repo
            cmd_pull = [GitClient._executable, 'pull', remote, command.version]
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
        if command.limit_tag:
            # check if specific tag exists
            cmd_tag = [GitClient._executable, 'tag', '-l', command.limit_tag]
            result_tag = self._run_command(cmd_tag)
            if result_tag['returncode']:
                return result_tag
            if not result_tag['output']:
                return {
                    'cmd': '',
                    'cwd': self.path,
                    'output': "Repository lacks the tag '%s'" % command.limit_tag,
                    'returncode': 1
                }
            # output log since specific tag
            cmd = [GitClient._executable, 'log', '%s..' % command.limit_tag]
        elif command.limit_untagged:
            # determine nearest tag
            cmd_tag = [GitClient._executable, 'describe', '--abbrev=0', '--tags']
            result_tag = self._run_command(cmd_tag)
            if result_tag['returncode']:
                return result_tag
            # output log since nearest tag
            cmd = [GitClient._executable, 'log', '%s..' % result_tag['output']]
        else:
            cmd = [GitClient._executable, 'log']
            if command.limit != 0:
                cmd += ['-%d' % command.limit]
        self._check_color(cmd)
        return self._run_command(cmd)

    def pull(self, _command):
        cmd = [GitClient._executable, 'pull']
        self._check_color(cmd)
        return self._run_command(cmd)

    def push(self, _command):
        cmd = [GitClient._executable, 'push']
        return self._run_command(cmd)

    def remotes(self, _command):
        cmd = [GitClient._executable, 'remote', '-v']
        return self._run_command(cmd)

    def status(self, command):
        if command.hide_empty:
            cmd = [GitClient._executable, 'status', '-s']
            if command.quiet:
                cmd += ['--untracked-files=no']
            result = self._run_command(cmd)
            if result['returncode'] or not result['output']:
                return result
        cmd = [GitClient._executable, 'status']
        self._check_color(cmd)
        if command.quiet:
            cmd += ['--untracked-files=no']
        return self._run_command(cmd)

    def _check_color(self, cmd):
        # check if user uses colorization
        if GitClient._config_color_is_auto is None:
            _cmd = [GitClient._executable, 'config', '--get', 'color.ui']
            result = self._run_command(_cmd)
            GitClient._config_color_is_auto = (result['output'] == 'auto')

        # inject arguments to force colorization
        if GitClient._config_color_is_auto:
            cmd[1:1] = '-c', 'color.ui=always'


if not GitClient._executable:
    GitClient._executable = find_executable('git')
