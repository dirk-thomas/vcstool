import os
import subprocess


class VcsClientBase(object):

    type = None

    def __init__(self, path):
        self.path = path

    def __getattribute__(self, name):
        if name == 'import':
            try:
                return self.import_
            except AttributeError:
                pass
        return super(VcsClientBase, self).__getattribute__(name)

    def _not_applicable(self, command):
        return {
            'cmd': '%s.%s(%s)' % (self.__class__.type, 'push', command.__class__.command),
            'output': "Command '%s' not applicable for client '%s'" % (command.__class__.command, self.__class__.type),
            'returncode': NotImplemented
        }

    def _run_command(self, cmd, env=None):
        return run_command(cmd, os.path.abspath(self.path), env=env)

    def _create_path(self):
        if not os.path.exists(self.path):
            try:
                os.makedirs(self.path)
            except os.error as e:
                return {
                    'cmd': 'os.makedirs(%s)' % self.path,
                    'cwd': self.path,
                    'output': "Could not create directory '%s': %s" % (self.path, e),
                    'returncode': 1
                }
        return None


def is_executable_file(file_path):
    return os.path.isfile(file_path) and os.access(file_path, os.X_OK)


def find_executable(file_name, check_for_exe=None):
    # If not explicitly set, True for Windows, otherwise False
    if check_for_exe is None:
        check_for_exe = os.name == 'nt'
    # Set to False if it already ends with .exe
    if check_for_exe:
        if file_name.endswith('.exe'):
            check_for_exe = False
    for path in os.getenv('PATH').split(os.path.pathsep):
        file_path = os.path.join(path, file_name)
        if is_executable_file(file_path):
            return file_path
        if check_for_exe:
            file_path += '.exe'
            if is_executable_file(file_path):
                return file_path
    return None


def run_command(cmd, cwd, env=None):
    result = {'cmd': ' '.join(cmd), 'cwd': cwd}
    try:
        proc = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
        output, _ = proc.communicate()
        result['output'] = output.rstrip().decode('utf8')
        result['returncode'] = proc.returncode
    except subprocess.CalledProcessError as e:
        result['output'] = e.output.decode('utf8')
        result['returncode'] = e.returncode
    return result
