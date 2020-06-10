import os

from vcstool.executor import USE_COLOR

from .vcs_base import VcsClientBase
from .vcs_base import which
from ..util import rmtree


class GitClient(VcsClientBase):

    type = 'git'
    _executable = None
    _config_color_is_auto = None

    @staticmethod
    def is_repository(path):
        return os.path.isdir(os.path.join(path, '.git'))

    def __init__(self, path):
        super(GitClient, self).__init__(path)

    def branch(self, command):
        self._check_executable()
        cmd = [GitClient._executable, 'branch']
        result = self._run_command(cmd)

        if not command.all and not result['returncode']:
            # only show current branch
            lines = result['output'].splitlines()
            lines = [line[2:] for line in lines if line.startswith('* ')]
            result['output'] = '\n'.join(lines)

        return result

    def custom(self, command):
        self._check_executable()
        cmd = [GitClient._executable] + command.args
        return self._run_command(cmd)

    def diff(self, command):
        self._check_executable()
        cmd = [GitClient._executable, 'diff']
        self._check_color(cmd)
        if command.context:
            cmd += ['--unified=%d' % command.context]
        return self._run_command(cmd)

    def export(self, command):
        self._check_executable()
        exact = command.exact
        if not exact:
            # determine if a specific branch is checked out or ec is detached
            cmd_branch = [
                GitClient._executable, 'rev-parse', '--abbrev-ref', 'HEAD']
            result_branch = self._run_command(cmd_branch)
            if result_branch['returncode']:
                result_branch['output'] = 'Could not determine ref: ' + \
                    result_branch['output']
                return result_branch
            branch_name = result_branch['output']
            exact = branch_name == 'HEAD'  # is detached

        if not exact:
            # determine the remote of the current branch
            cmd_remote = [
                GitClient._executable, 'rev-parse', '--abbrev-ref',
                '@{upstream}']
            result_remote = self._run_command(cmd_remote)
            if result_remote['returncode']:
                result_remote['output'] = 'Could not determine ref: ' + \
                    result_remote['output']
                return result_remote
            branch_with_remote = result_remote['output']

            # determine remote
            suffix = '/' + branch_name
            assert branch_with_remote.endswith(branch_name), \
                "'%s' does not end with '%s'" % \
                (branch_with_remote, branch_name)
            remote = branch_with_remote[:-len(suffix)]

            # if a local ref exists with the same name as the remote branch
            # the result will be prefixed to make it unambiguous
            prefix = 'remotes/'
            if remote.startswith(prefix):
                remote = remote[len(prefix):]

            # determine url of remote
            result_url = self._get_remote_url(remote)
            if result_url['returncode']:
                return result_url
            url = result_url['output']

            # the result is the remote url and the branch name
            return {
                'cmd': ' && '.join([
                    result_branch['cmd'], result_remote['cmd'],
                    result_url['cmd']]),
                'cwd': self.path,
                'output': '\n'.join([url, branch_name]),
                'returncode': 0,
                'export_data': {'url': url, 'version': branch_name}
            }

        else:
            # determine the hash
            cmd_ref = [GitClient._executable, 'rev-parse', 'HEAD']
            result_ref = self._run_command(cmd_ref)
            if result_ref['returncode']:
                result_ref['output'] = 'Could not determine ref: ' + \
                    result_ref['output']
                return result_ref
            ref = result_ref['output']

            # get all remote names
            cmd_remotes = [GitClient._executable, 'remote']
            result_remotes = self._run_command(cmd_remotes)
            if result_remotes['returncode']:
                result_remotes['output'] = 'Could not determine remotes: ' + \
                    result_remotes['output']
                return result_remotes
            remotes = result_remotes['output'].splitlines()

            # prefer origin and upstream remotes
            if 'upstream' in remotes:
                remotes.remove('upstream')
                remotes.insert(0, 'upstream')
            if 'origin' in remotes:
                remotes.remove('origin')
                remotes.insert(0, 'origin')

            # for each remote name check if the hash is part of the remote
            for remote in remotes:
                # get all remote names
                cmd_refs = [
                    GitClient._executable, 'rev-list', '--remotes=' + remote,
                    '--tags']
                result_refs = self._run_command(cmd_refs)
                if result_refs['returncode']:
                    result_refs['output'] = \
                        "Could not determine refs of remote '%s': " % \
                        remote + result_refs['output']
                    return result_refs
                refs = result_refs['output'].splitlines()
                if ref not in refs:
                    continue

                cmds = [result_ref['cmd']]
                if command.with_tags:
                    # check if there is exactly one tag pointing to that ref
                    cmd_tags = [
                        GitClient._executable, 'tag', '--points-at', ref]
                    result_tags = self._run_command(cmd_tags)
                    if result_tags['returncode']:
                        result_tags['output'] = \
                            "Could not determine tags for ref '%s': " % \
                            ref + result_tags['output']
                        return result_tags
                    cmds.append(result_tags['cmd'])
                    tags = result_tags['output'].splitlines()
                    if len(tags) == 1:
                        tag = tags[0]
                        # double check that the tag is part of the remote
                        # and references the same hash
                        cmd_ls_remote = [
                            GitClient._executable, 'ls-remote', remote,
                            'refs/tags/' + tag]
                        result_ls_remote = self._run_command(cmd_ls_remote)
                        if result_ls_remote['returncode']:
                            result_ls_remote['output'] = \
                                "Could not check remote tags for '%s': " % \
                                remote + result_ls_remote['output']
                            return result_ls_remote
                        matches = result_ls_remote['output'].splitlines()
                        if len(matches) == 1 and matches[0].split()[0] == ref:
                            ref = tag

                # determine url of remote
                result_url = self._get_remote_url(remote)
                if result_url['returncode']:
                    return result_url
                url = result_url['output']
                cmds.append(result_url['cmd'])

                # the result is the remote url and the hash/tag
                return {
                    'cmd': ' && '.join(cmds),
                    'cwd': self.path,
                    'output': '\n'.join([url, ref]),
                    'returncode': 0,
                    'export_data': {'url': url, 'version': ref}
                }

            return {
                'cmd': ' && '.join([result_ref['cmd'], result_remotes['cmd']]),
                'cwd': self.path,
                'output': "Could not determine remote containing '%s'" % ref,
                'returncode': 1,
            }

    def _get_remote_url(self, remote):
        cmd_url = [
            GitClient._executable, 'config', '--get', 'remote.%s.url' % remote]
        result_url = self._run_command(cmd_url)
        if result_url['returncode']:
            result_url['output'] = 'Could not determine remote url: ' + \
                result_url['output']
        return result_url

    def import_(self, command):
        if not command.url:
            return {
                'cmd': '',
                'cwd': self.path,
                'output': "Repository data lacks the 'url' value",
                'returncode': 1
            }

        self._check_executable()
        if GitClient.is_repository(self.path):
            # verify that existing repository is the same
            result_urls = self._get_remote_urls()
            if result_urls['returncode']:
                return result_urls
            for url, remote in result_urls['output']:
                if url == command.url:
                    break
            else:
                if command.skip_existing:
                    return {
                        'cmd': '',
                        'cwd': self.path,
                        'output':
                            'Skipped existing repository with different URL',
                        'returncode': 0
                    }
                if not command.force:
                    return {
                        'cmd': '',
                        'cwd': self.path,
                        'output':
                            'Path already exists and contains a different '
                            'repository',
                        'returncode': 1
                    }
                try:
                    rmtree(self.path)
                except OSError:
                    os.remove(self.path)

        elif command.skip_existing and os.path.exists(self.path):
            return {
                'cmd': '',
                'cwd': self.path,
                'output': 'Skipped existing directory',
                'returncode': 0
            }

        elif command.force and os.path.exists(self.path):
            # Not empty, not a git repository
            try:
                rmtree(self.path)
            except OSError:
                os.remove(self.path)

        not_exist = self._create_path()
        if not_exist:
            return not_exist

        if GitClient.is_repository(self.path):
            if command.skip_existing:
                checkout_version = None
            elif command.version:
                checkout_version = command.version
            else:
                # determine remote HEAD branch
                cmd_remote = [GitClient._executable, 'remote', 'show', remote]
                # override locale in order to parse output
                env = os.environ.copy()
                env['LC_ALL'] = 'C'
                result_remote = self._run_command(cmd_remote, env=env)
                if result_remote['returncode']:
                    result_remote['output'] = \
                        'Could not get remote information of repository ' \
                        "'%s': %s" % (url, result_remote['output'])
                    return result_remote
                prefix = '  HEAD branch: '
                for line in result_remote['output'].splitlines():
                    if line.startswith(prefix):
                        checkout_version = line[len(prefix):]
                        break
                else:
                    result_remote['returncode'] = 1
                    result_remote['output'] = \
                        'Could not determine remote HEAD branch of ' \
                        "repository '%s': %s" % (url, result_remote['output'])
                    return result_remote

            # fetch updates for existing repo
            cmd_fetch = [GitClient._executable, 'fetch', remote]
            if command.shallow:
                result_version_type = self._check_version_type(
                    command.url, checkout_version)
                if result_version_type['returncode']:
                    return result_version_type
                version_type = result_version_type['version_type']
                if version_type == 'branch':
                    cmd_fetch.append(
                        'refs/heads/%s:refs/remotes/%s/%s' %
                        (checkout_version, remote, checkout_version))
                elif version_type == 'hash':
                    cmd_fetch.append(checkout_version)
                elif version_type == 'tag':
                    cmd_fetch.append(
                        '+refs/tags/%s:refs/tags/%s' %
                        (checkout_version, checkout_version))
                else:
                    assert False
                cmd_fetch += ['--depth', '1']
            result_fetch = self._run_command(cmd_fetch, retry=command.retry)
            if result_fetch['returncode']:
                return result_fetch
            cmd = result_fetch['cmd']
            output = result_fetch['output']

            # ensure that a tracking branch exists which can be checked out
            if command.shallow and version_type == 'branch':
                cmd_show_ref = [
                    GitClient._executable, 'show-ref',
                    'refs/heads/%s' % checkout_version]
                result_show_ref = self._run_command(cmd_show_ref)
                if result_show_ref['returncode']:
                    # creating tracking branch
                    cmd_branch = [
                        GitClient._executable, 'branch', checkout_version,
                        '%s/%s' % (remote, checkout_version)]
                    result_branch = self._run_command(cmd_branch)
                    if result_branch['returncode']:
                        result_branch['output'] = \
                            "Could not create branch '%s': %s" % \
                            (checkout_version, result_branch['output'])
                        return result_branch
                    cmd += ' && ' + ' '.join(cmd_branch)
                    output = '\n'.join([output, result_branch['output']])

        else:
            version_type = None
            if command.version:
                result_version_type = self._check_version_type(
                    command.url, command.version)
                if result_version_type['returncode']:
                    return result_version_type
                version_type = result_version_type['version_type']

            if not command.shallow or version_type in (None, 'branch'):
                cmd_clone = [GitClient._executable, 'clone', command.url, '.']
                if version_type == 'branch':
                    cmd_clone += ['-b', command.version]
                    checkout_version = None
                else:
                    checkout_version = command.version
                if command.shallow:
                    cmd_clone += ['--depth', '1']
                result_clone = self._run_command(
                    cmd_clone, retry=command.retry)
                if result_clone['returncode']:
                    result_clone['output'] = \
                        "Could not clone repository '%s': %s" % \
                        (command.url, result_clone['output'])
                    return result_clone
                cmd = result_clone['cmd']
                output = result_clone['output']
            else:
                # getting a hash or tag with a depth of 1 can't use 'clone'
                cmd_init = [GitClient._executable, 'init']
                result_init = self._run_command(cmd_init)
                if result_init['returncode']:
                    return result_init
                cmd = result_init['cmd']
                output = result_init['output']

                cmd_remote_add = [
                    GitClient._executable, 'remote', 'add', 'origin',
                    command.url]
                result_remote_add = self._run_command(cmd_remote_add)
                if result_remote_add['returncode']:
                    return result_remote_add
                cmd += ' && ' + ' '.join(cmd_remote_add)
                output = '\n'.join([output, result_remote_add['output']])

                cmd_fetch = [GitClient._executable, 'fetch', 'origin']
                if version_type == 'hash':
                    cmd_fetch.append(command.version)
                elif version_type == 'tag':
                    cmd_fetch.append(
                        'refs/tags/%s:refs/tags/%s' %
                        (command.version, command.version))
                else:
                    assert False
                cmd_fetch += ['--depth', '1']
                result_fetch = self._run_command(
                    cmd_fetch, retry=command.retry)
                if result_fetch['returncode']:
                    return result_fetch
                cmd += ' && ' + ' '.join(cmd_fetch)
                output = '\n'.join([output, result_fetch['output']])

                checkout_version = command.version

        if checkout_version:
            cmd_checkout = [
                GitClient._executable, 'checkout', checkout_version, '--']
            result_checkout = self._run_command(cmd_checkout)
            if result_checkout['returncode']:
                result_checkout['output'] = \
                    "Could not checkout ref '%s': %s" % \
                    (checkout_version, result_checkout['output'])
                return result_checkout
            cmd += ' && ' + ' '.join(cmd_checkout)
            output = '\n'.join([output, result_checkout['output']])

        if command.recursive:
            cmd_submodule = [
                GitClient._executable, 'submodule', 'update', '--init']
            result_submodule = self._run_command(cmd_submodule)
            if result_submodule['returncode']:
                result_submodule['output'] = \
                    'Could not init/update submodules: %s' % \
                    result_submodule['output']
                return result_submodule
            cmd += ' && ' + ' '.join(cmd_submodule)
            output = '\n'.join([output, result_submodule['output']])

        return {
            'cmd': cmd,
            'cwd': self.path,
            'output': output,
            'returncode': 0
        }

    def _get_remote_urls(self):
        cmd_remote = [GitClient._executable, 'remote', 'show']
        result_remote = self._run_command(cmd_remote)
        if result_remote['returncode']:
            result_remote['output'] = 'Could not determine remotes: ' + \
                result_remote['output']
            return result_remote
        remote_urls = []
        cmd = result_remote['cmd']
        for remote in result_remote['output'].splitlines():
            result_url = self._get_remote_url(remote)
            cmd += ' && ' + result_url['cmd']
            if not result_url['returncode']:
                remote_urls.append((result_url['output'], remote))
        return {
            'cmd': cmd,
            'cwd': self.path,
            'output': (remote_urls if remote_urls else
                       'Could not determine any of the remote urls'),
            'returncode': 0 if remote_urls else 1
        }

    def _check_version_type(self, url, version):
        cmd = [GitClient._executable, 'ls-remote', url, version]
        result = self._run_command(cmd)
        if result['returncode']:
            result['output'] = 'Could not determine ref type of version: ' + \
                result['output']
            return result
        if not result['output']:
            result['version_type'] = 'hash'
            return result

        refs = {}
        for line in result['output'].splitlines():
            hash_, ref = line.split(None, 1)
            refs[ref] = hash_

        tag_ref = 'refs/tags/' + version
        branch_ref = 'refs/heads/' + version
        if tag_ref in refs and branch_ref in refs:
            if refs[tag_ref] != refs[branch_ref]:
                result['returncode'] = 1
                result['output'] = 'The version ref is a branch as well as ' \
                    'tag but with different hashes'
                return result
        if tag_ref in refs:
            result['version_type'] = 'tag'
        elif branch_ref in refs:
            result['version_type'] = 'branch'
        else:
            result['returncode'] = 1
            result['output'] = 'Could not determine ref type of version: ' + \
                result['output']
        return result

    def log(self, command):
        self._check_executable()
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
                    'output':
                        "Repository lacks the tag '%s'" % command.limit_tag,
                    'returncode': 1
                }
            # output log since specific tag
            cmd = [GitClient._executable, 'log', '%s..' % command.limit_tag]
        elif command.limit_untagged:
            # determine nearest tag
            cmd_tag = [
                GitClient._executable, 'describe', '--abbrev=0', '--tags']
            result_tag = self._run_command(cmd_tag)
            if result_tag['returncode']:
                return result_tag
            # output log since nearest tag
            cmd = [GitClient._executable, 'log', '%s..' % result_tag['output']]
        else:
            cmd = [GitClient._executable, 'log']
        cmd += ['--decorate']
        if command.limit != 0:
            cmd += ['-%d' % command.limit]
        if not command.verbose:
            cmd += ['--pretty=short']
        self._check_color(cmd)
        return self._run_command(cmd)

    def pull(self, _command):
        self._check_executable()
        cmd = [GitClient._executable, 'pull']
        self._check_color(cmd)
        return self._run_command(cmd)

    def push(self, _command):
        self._check_executable()
        cmd = [GitClient._executable, 'push']
        return self._run_command(cmd)

    def remotes(self, _command):
        self._check_executable()
        cmd = [GitClient._executable, 'remote', '-v']
        return self._run_command(cmd)

    def status(self, command):
        self._check_executable()
        while command.hide_empty:
            # check if ahead
            cmd = [GitClient._executable, 'log', '@{push}..']
            result = self._run_command(cmd)
            if not result['returncode'] and result['output']:
                # ahead, do not hide
                break
            # check if behind
            cmd = [GitClient._executable, 'log', '..@{upstream}']
            result = self._run_command(cmd)
            if not result['returncode'] and result['output']:
                # behind, do not hide
                break
            cmd = [GitClient._executable, 'status', '-s']
            if command.quiet:
                cmd += ['--untracked-files=no']
            result = self._run_command(cmd)
            if result['returncode'] or not result['output']:
                return result
            break
        cmd = [GitClient._executable, 'status']
        self._check_color(cmd)
        if command.quiet:
            cmd += ['--untracked-files=no']
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

        cmd_ls_remote = [GitClient._executable, 'ls-remote']
        cmd_ls_remote += ['-q', '--exit-code']
        cmd_ls_remote += [command.url]
        env = os.environ.copy()
        env['GIT_TERMINAL_PROMPT'] = '0'
        result_ls_remote = self._run_command(
            cmd_ls_remote,
            retry=command.retry,
            env=env)
        if result_ls_remote['returncode']:
            result_ls_remote['output'] = \
                "Failed to contact remote repository '%s': %s" % \
                (command.url, result_ls_remote['output'])
            return result_ls_remote

        if command.version:
            hashes = []
            refs = []
            output_lines = result_ls_remote['output'].splitlines()

            for line in output_lines:
                hash_and_ref = line.split()
                hashes.append(hash_and_ref[0])

                # ignore pull request refs
                if not hash_and_ref[1].startswith('refs/pull/'):
                    if hash_and_ref[1].startswith('refs/tags/'):
                        refs.append(hash_and_ref[1][10:])
                    elif hash_and_ref[1].startswith('refs/heads/'):
                        refs.append(hash_and_ref[1][11:])
                    else:
                        refs.append(hash_and_ref[1])

            # test for refs first
            ref_found = command.version in refs

            if not ref_found:
                for _hash in hashes:
                    if _hash.startswith(command.version):
                        ref_found = True
                        break

            if not ref_found:
                cmd = result_ls_remote['cmd']
                output = "Found git repository '%s' but " % command.url + \
                    'unable to verify non-branch / non-tag ref ' + \
                    "'%s' without cloning the repo" % command.version

                return {
                    'cmd': cmd,
                    'cwd': self.path,
                    'output': output,
                    'returncode': 0
                }
            else:
                cmd = result_ls_remote['cmd']
                output = "Found git repository '%s' with ref '%s'" % \
                    (command.url, command.version)
        else:
            cmd = result_ls_remote['cmd']
            output = "Found git repository '%s' with default branch" % \
                command.url

        return {
            'cmd': cmd,
            'cwd': self.path,
            'output': output,
            'returncode': None
        }

    def _check_color(self, cmd):
        if not USE_COLOR:
            return
        # check if user uses colorization
        if GitClient._config_color_is_auto is None:
            _cmd = [GitClient._executable, 'config', '--get', 'color.ui']
            result = self._run_command(_cmd)
            GitClient._config_color_is_auto = result['output'] in ['', 'auto']

        # inject arguments to force colorization
        if GitClient._config_color_is_auto:
            cmd[1:1] = '-c', 'color.ui=always'

    def _check_executable(self):
        assert GitClient._executable is not None, \
            "Could not find 'git' executable"


if not GitClient._executable:
    GitClient._executable = which('git')
