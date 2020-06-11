import os
import subprocess
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from vcstool.util import rmtree  # noqa: E402

REPOS_FILE = os.path.join(os.path.dirname(__file__), 'list.repos')
REPOS2_FILE = os.path.join(os.path.dirname(__file__), 'list2.repos')
TEST_WORKSPACE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), 'test_workspace')


class TestCommands(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        assert not os.path.exists(TEST_WORKSPACE)
        os.makedirs(TEST_WORKSPACE)

        try:
            output = run_command(
                'import', ['--input', REPOS_FILE, '.'])
            expected = get_expected_output('import')
            # newer git versions don't append three dots after the commit hash
            assert output == expected or \
                output == expected.replace(b'... ', b' ')
        except Exception:
            cls.tearDownClass()
            raise

    @classmethod
    def tearDownClass(cls):
        rmtree(TEST_WORKSPACE)

    def test_branch(self):
        output = run_command('branch')
        expected = get_expected_output('branch')
        self.assertEqual(output, expected)

    def test_custom(self):
        output = run_command(
            'custom',
            args=['--git', '--args', 'describe', '--abbrev=0', '--tags'],
            subfolder='immutable')
        expected = get_expected_output('custom_describe')
        self.assertEqual(output, expected)

    def test_diff(self):
        license_path = os.path.join(
            TEST_WORKSPACE, 'immutable', 'hash', 'LICENSE')
        file_length = None
        try:
            with open(license_path, 'ab') as h:
                file_length = h.tell()
                h.write(b'testing')

            output = run_command('diff', args=['--hide'])
            expected = get_expected_output('diff_hide')
        finally:
            if file_length is not None:
                with open(license_path, 'ab') as h:
                    h.truncate(file_length)

        self.assertEqual(output, expected)

    def test_export_exact_with_tags(self):
        output = run_command(
            'export',
            args=['--exact-with-tags'],
            subfolder='immutable')
        expected = get_expected_output('export_exact_with_tags')
        self.assertEqual(output, expected)

    def test_export_exact(self):
        output = run_command(
            'export',
            args=['--exact'],
            subfolder='immutable')
        expected = get_expected_output('export_exact')
        self.assertEqual(output, expected)

    def test_log(self):
        output = run_command(
            'log', args=['--limit', '2'], subfolder='immutable')
        expected = get_expected_output('log_limit')
        self.assertEqual(output, expected)

    def test_pull(self):
        with self.assertRaises(subprocess.CalledProcessError) as e:
            run_command('pull', args=['--workers', '1'])
        expected = get_expected_output('pull')
        # replace message from older git versions
        output = e.exception.output.replace(
            b'anch. Please specify which\nbranch you want to merge with. See',
            b'anch.\nPlease specify which branch you want to merge with.\nSee')
        # newer git versions warn on pull with default config
        if _get_git_version() >= [2, 27, 0]:
            pull_warning = b"""
warning: Pulling without specifying how to reconcile divergent branches is
discouraged. You can squelch this message by running one of the following
commands sometime before your next pull:

  git config pull.rebase false  # merge (the default strategy)
  git config pull.rebase true   # rebase
  git config pull.ff only       # fast-forward only

You can replace "git config" with "git config --global" to set a default
preference for all repositories. You can also pass --rebase, --no-rebase,
or --ff-only on the command line to override the configured default per
invocation.
"""
            output = output.replace(pull_warning, b'')
        self.assertEqual(output, expected)

    def test_pull_api(self):
        try:
            from cStringIO import StringIO
        except ImportError:
            from io import StringIO
        from vcstool.commands.pull import main
        stdout_stderr = StringIO()

        # change and restore cwd
        cwd_bck = os.getcwd()
        os.chdir(TEST_WORKSPACE)
        try:
            # change and restore USE_COLOR flag
            from vcstool import executor
            use_color_bck = executor.USE_COLOR
            executor.USE_COLOR = False
            try:
                # change and restore os.environ
                env_bck = os.environ
                os.environ = dict(os.environ)
                os.environ.update(
                    LANG='en_US.UTF-8',
                    PYTHONPATH=(
                        os.path.dirname(os.path.dirname(__file__)) +
                        os.pathsep + os.environ.get('PYTHONPATH', '')))
                try:
                    rc = main(
                        args=['--workers', '1'],
                        stdout=stdout_stderr, stderr=stdout_stderr)
                finally:
                    os.environ = env_bck
            finally:
                executor.USE_COLOR = use_color_bck
        finally:
            os.chdir(cwd_bck)

        assert rc == 1
        # replace message from older git versions
        output = stdout_stderr.getvalue().replace(
            'anch. Please specify which\nbranch you want to merge with. See',
            'anch.\nPlease specify which branch you want to merge with.\nSee')
        # newer git versions warn on pull with default config
        if _get_git_version() >= [2, 27, 0]:
            pull_warning = """
warning: Pulling without specifying how to reconcile divergent branches is
discouraged. You can squelch this message by running one of the following
commands sometime before your next pull:

  git config pull.rebase false  # merge (the default strategy)
  git config pull.rebase true   # rebase
  git config pull.ff only       # fast-forward only

You can replace "git config" with "git config --global" to set a default
preference for all repositories. You can also pass --rebase, --no-rebase,
or --ff-only on the command line to override the configured default per
invocation.
"""
            output = output.replace(pull_warning, '')
        expected = get_expected_output('pull').decode()
        assert output == expected

    def test_reimport(self):
        cwd_vcstool = os.path.join(TEST_WORKSPACE, 'vcstool')
        subprocess.check_output(
            ['git', 'remote', 'add', 'foo', 'http://foo.com/bar.git'],
            stderr=subprocess.STDOUT, cwd=cwd_vcstool)
        cwd_without_version = os.path.join(TEST_WORKSPACE, 'without_version')
        subprocess.check_output(
            ['git', 'checkout', '-b', 'foo'],
            stderr=subprocess.STDOUT, cwd=cwd_without_version)
        output = run_command(
            'import', ['--skip-existing', '--input', REPOS_FILE, '.'])
        expected = get_expected_output('reimport_skip')
        # newer git versions don't append three dots after the commit hash
        assert output == expected or output == expected.replace(b'... ', b' ')

        subprocess.check_output(
            ['git', 'remote', 'set-url', 'origin', 'http://foo.com/bar.git'],
            stderr=subprocess.STDOUT, cwd=cwd_without_version)
        try:
            run_command(
                'import', ['--skip-existing', '--input', REPOS_FILE, '.'])
            # The run_command function should raise an exception when the
            # process returns a non-zero return code, so the next line should
            # never get executed.
            assert False
        except BaseException:
            pass

        output = run_command(
            'import', ['--force', '--input', REPOS_FILE, '.'])
        expected = get_expected_output('reimport_force')
        # newer git versions don't append three dots after the commit hash
        assert output == expected or output == expected.replace(b'... ', b' ')

        subprocess.check_output(
            ['git', 'remote', 'remove', 'foo'],
            stderr=subprocess.STDOUT, cwd=cwd_vcstool)

    def test_reimport_failed(self):
        cwd_tag = os.path.join(TEST_WORKSPACE, 'immutable', 'tag')
        subprocess.check_output(
            ['git', 'remote', 'add', 'foo', 'http://foo.com/bar.git'],
            stderr=subprocess.STDOUT, cwd=cwd_tag)
        subprocess.check_output(
            ['git', 'remote', 'rm', 'origin'],
            stderr=subprocess.STDOUT, cwd=cwd_tag)
        try:
            run_command(
                'import', ['--skip-existing', '--input', REPOS_FILE, '.'])
            # The run_command function should raise an exception when the
            # process returns a non-zero return code, so the next line should
            # never get executed.
            assert False
        except BaseException:
            pass
        finally:
            subprocess.check_output(
                ['git', 'remote', 'rm', 'foo'],
                stderr=subprocess.STDOUT, cwd=cwd_tag)
            subprocess.check_output(
                ['git', 'remote', 'add', 'origin',
                 'https://github.com/dirk-thomas/vcstool.git'],
                stderr=subprocess.STDOUT, cwd=cwd_tag)

    def test_import_force_non_empty(self):
        workdir = os.path.join(TEST_WORKSPACE, 'force-non-empty')
        os.makedirs(os.path.join(workdir, 'vcstool', 'not-a-git-repo'))
        try:
            output = run_command(
                'import', ['--force', '--input', REPOS_FILE, '.'],
                subfolder='force-non-empty')
            expected = get_expected_output('import')
            # newer git versions don't append ... after the commit hash
            assert (
                output == expected or
                output == expected.replace(b'... ', b' '))
        finally:
            rmtree(workdir)

    def test_import_shallow(self):
        workdir = os.path.join(TEST_WORKSPACE, 'import-shallow')
        os.makedirs(workdir)
        try:
            output = run_command(
                'import', ['--shallow', '--input', REPOS_FILE, '.'],
                subfolder='import-shallow')
            # the actual output contains absolute paths
            output = output.replace(
                b'repository in ' + workdir.encode() + b'/',
                b'repository in ./')
            expected = get_expected_output('import_shallow')
            # newer git versions don't append ... after the commit hash
            assert (
                output == expected or
                output == expected.replace(b'... ', b' '))

            # check that repository history has only one commit
            output = subprocess.check_output(
                ['git', 'log', '--format=oneline'],
                stderr=subprocess.STDOUT, cwd=os.path.join(workdir, 'vcstool'))
            assert len(output.splitlines()) == 1
        finally:
            rmtree(workdir)

    def test_validate(self):
        output = run_command(
            'validate', ['--input', REPOS_FILE])
        expected = get_expected_output('validate')
        self.assertEqual(output, expected)

        output = run_command(
            'validate', ['--input', REPOS2_FILE])
        expected = get_expected_output('validate2')
        self.assertEqual(output, expected)

        output = run_command(
            'validate', ['--hide-empty', '--input', REPOS_FILE])
        expected = get_expected_output('validate_hide')
        self.assertEqual(output, expected)

    def test_remote(self):
        output = run_command('remotes', args=['--repos'])
        expected = get_expected_output('remotes_repos')
        self.assertEqual(output, expected)

    def test_status(self):
        output = run_command('status')
        # replace message from older git versions
        # https://github.com/git/git/blob/3ec7d702a89c647ddf42a59bc3539361367de9d5/Documentation/RelNotes/2.10.0.txt#L373-L374
        output = output.replace(
            b'working directory clean', b'working tree clean')
        # the following seems to have changed between git 2.10.0 and 2.14.1
        output = output.replace(
            b'.\nnothing to commit', b'.\n\nnothing to commit')
        expected = get_expected_output('status')
        self.assertEqual(output, expected)


def run_command(command, args=None, subfolder=None):
    repo_root = os.path.dirname(os.path.dirname(__file__))
    script = os.path.join(repo_root, 'scripts', 'vcs-' + command)
    env = dict(os.environ)
    env.update(
        LANG='en_US.UTF-8',
        PYTHONPATH=repo_root + os.pathsep + env.get('PYTHONPATH', ''))
    cwd = TEST_WORKSPACE
    if subfolder:
        cwd = os.path.join(cwd, subfolder)
    output = subprocess.check_output(
        [sys.executable, script] + (args or []),
        stderr=subprocess.STDOUT, cwd=cwd, env=env)
    # replace message from older git versions
    output = output.replace(
        b'git checkout -b new_branch_name',
        b'git checkout -b <new-branch-name>')
    output = output.replace(
        b'(detached from ', b'(HEAD detached at ')
    output = output.replace(
        b"ady on 'master'\n=",
        b"ady on 'master'\nYour branch is up-to-date with 'origin/master'.\n=")
    output = output.replace(
        b'# HEAD detached at ',
        b'HEAD detached at ')
    output = output.replace(
        b'# On branch master',
        b"On branch master\nYour branch is up-to-date with 'origin/master'.\n")
    # the following seems to have changed between git 2.17.1 and 2.25.1
    output = output.replace(
        b"Note: checking out '", b"Note: switching to '")
    output = output.replace(
        b'by performing another checkout.',
        b'by switching back to a branch.')
    output = output.replace(
        b'using -b with the checkout command again.',
        b'using -c with the switch command.')
    output = output.replace(
        b'git checkout -b <new-branch-name>',
        b'git switch -c <new-branch-name>\n\n'
        b'Or undo this operation with:\n\n'
        b'  git switch -\n\n'
        b'Turn off this advice by setting config variable '
        b'advice.detachedHead to false')
    # replace GitHub SSH clone URL
    output = output.replace(
        b'git@github.com:', b'https://github.com/')
    return output


def get_expected_output(name):
    path = os.path.join(os.path.dirname(__file__), name + '.txt')
    with open(path, 'rb') as h:
        content = h.read()
    # change in git version 2.15.0
    # https://github.com/git/git/commit/7560f547e6
    if _get_git_version() < [2, 15, 0]:
        # use hyphenation for older git versions
        content = content.replace(b'up to date', b'up-to-date')
    return content


def _get_git_version():
    output = subprocess.check_output(['git', '--version'])
    prefix = b'git version '
    assert output.startswith(prefix)
    output = output[len(prefix):].rstrip()
    return [int(x) for x in output.split(b'.') if x != b'windows']


if __name__ == '__main__':
    unittest.main()
