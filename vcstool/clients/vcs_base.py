import os
import subprocess


class VcsClientBase(object):

    type = None

    def __init__(self, path):
        self.path = path

    def _run_command(self, cmd):
        return run_command(cmd, os.path.abspath(self.path))


def find_executable(file_name):
    for path in os.getenv('PATH').split(os.path.pathsep):
        file_path = os.path.join(path, file_name)
        if os.path.isfile(file_path):
            return file_path
    return None


def run_command(cmd, cwd):
    result = {'cmd': ' '.join(cmd), 'cwd': cwd}
    try:
        result['output'] = subprocess.check_output(cmd, cwd=cwd, stderr=subprocess.STDOUT).rstrip()
        result['returncode'] = 0
    except subprocess.CalledProcessError as e:
        result['output'] = e.output
        result['returncode'] = e.returncode
    return result
