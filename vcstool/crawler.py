import os

from . import vcstool_clients


def find_repositories(path):
    repos = []
    client = get_vcs_client(path)
    if client:
        repos.append(client)
    else:
        try:
            listdir = os.listdir(path)
        except OSError:
            listdir = []
        for name in listdir:
            subpath = os.path.join(path, name)
            if not os.path.isdir(subpath):
                continue
            repos += find_repositories(subpath)
    return repos


def get_vcs_client(path):
    for vcs_type in vcstool_clients:
        if vcs_type.is_repository(path):
            return vcs_type(path)
    return None
