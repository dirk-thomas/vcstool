import os


class VcsClientBase(object):

    def __init__(self, vcs_type, path):
        self.type = vcs_type
        self.path = path


def find_executable(file_name):
    for path in os.getenv('PATH').split(os.path.pathsep):
        file_path = os.path.join(path, file_name)
        if os.path.isfile(file_path):
            return file_path
    return None
