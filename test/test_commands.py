import os
import shutil
import subprocess
import sys
import unittest


REPOS_FILE = os.path.join(os.path.dirname(__file__), 'list.repos')
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
            assert output == expected
        except Exception:
            cls.tearDownClass()
            raise

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEST_WORKSPACE)

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

    def test_export(self):
        output = run_command('export', args=['--exact'], subfolder='immutable')
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
        self.assertEqual(e.exception.output, expected)

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
    return subprocess.check_output(
        [sys.executable, script] + (args or []),
        stderr=subprocess.STDOUT, cwd=cwd, env=env)


def get_expected_output(name):
    path = os.path.join(os.path.dirname(__file__), name + '.txt')
    with open(path, 'rb') as h:
        return h.read()


if __name__ == '__main__':
    unittest.main()
