import os

from . import vcstool_clients


def find_repositories(paths):
    repos = []
    visited = []
    for path in paths:
        _find_repositories(path, repos, visited)
    return repos


def _find_repositories(path, repos, visited):
    abs_path = os.path.abspath(path)
    if abs_path in visited:
        return
    visited.append(abs_path)

    client = get_vcs_client(path)
    if client:
        repos.append(client)
    else:
        try:
            listdir = os.listdir(path)
        except OSError:
            listdir = []
        for name in sorted(listdir):
            subpath = os.path.join(path, name)
            if not os.path.isdir(subpath):
                continue
            _find_repositories(subpath, repos, visited)


def get_vcs_client(path):
    for client_class in vcstool_clients:
        if client_class.is_repository(path):
            return client_class(path)
    return None
