import os
import subprocess
import sys
import unittest


class TestOptions(unittest.TestCase):

    def test_clients(self):
        output = run_command(['--clients'])
        expected = get_expected_output('clients')
        self.assertEqual(output, expected)

    def test_commands(self):
        output = run_command(['--commands'])
        expected = get_expected_output('commands')
        self.assertEqual(output, expected)


def run_command(args):
    repo_root = os.path.dirname(os.path.dirname(__file__))
    script = os.path.join(repo_root, 'scripts', 'vcs')
    env = dict(os.environ)
    env.update(
        LANG='en_US.UTF-8',
        PYTHONPATH=repo_root + os.pathsep + env.get('PYTHONPATH', ''))
    return subprocess.check_output(
        [sys.executable, script] + (args or []),
        stderr=subprocess.STDOUT, env=env)


def get_expected_output(name):
    path = os.path.join(os.path.dirname(__file__), name + '.txt')
    with open(path, 'rb') as h:
        return h.read()


if __name__ == '__main__':
    unittest.main()
