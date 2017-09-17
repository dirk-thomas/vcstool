from __future__ import print_function

import argparse
import os
import sys

from vcstool.clients import vcstool_clients
from vcstool.executor import ansi, execute_jobs, output_repositories, output_results
import yaml

from .command import add_common_arguments, Command


class ImportCommand(Command):

    command = 'import'
    help = 'Import the list of repositories'

    def __init__(self, args, url, version=None):
        super(ImportCommand, self).__init__(args)
        self.url = url
        self.version = version
        self.force = args.force
        self.retry = args.retry


def get_parser():
    parser = argparse.ArgumentParser(description='Import the list of repositories', prog='vcs import')
    group = parser.add_argument_group('"import" command parameters')
    group.add_argument('--input', type=argparse.FileType('r'), default=sys.stdin)
    group.add_argument('--force', action='store_true', default=False, help='Potentially overwrite existing folders if they contain different repositories')
    group.add_argument('--retry', type=int, metavar='N', default=2, help='Retry commands requiring network access N times on failure')
    return parser


def get_repositories(yaml_file):
    try:
        root = yaml.load(yaml_file)
    except yaml.YAMLError as e:
        raise RuntimeError('Input data is not valid yaml format: %s' % e)

    try:
        repositories = root['repositories']
        return get_repos_in_vcstool_format(repositories)
    except AttributeError as e:
        raise RuntimeError('Input data is not valid format: %s' % e)
    except TypeError as e:
        # try rosinstall file format
        try:
            return get_repos_in_rosinstall_format(root)
        except Exception:
            raise RuntimeError('Input data is not valid format: %s' % e)


def get_repos_in_vcstool_format(repositories):
    repos = {}
    for path in repositories:
        repo = {}
        attributes = repositories[path]
        try:
            repo['type'] = attributes['type']
            repo['url'] = attributes['url']
            if 'version' in attributes:
                repo['version'] = attributes['version']
        except AttributeError as e:
            print(ansi('yellowf') + ("Repository '%s' does not provide the necessary information: %s" % (path, e)) + ansi('reset'), file=sys.stderr)
            continue
        repos[path] = repo
    return repos


def get_repos_in_rosinstall_format(root):
    repos = {}
    for i, item in enumerate(root):
        if len(item.keys()) != 1:
            raise RuntimeError('Input data is not valid format')
        repo = {'type': list(item.keys())[0]}
        attributes = list(item.values())[0]
        try:
            path = attributes['local-name']
        except AttributeError as e:
            print(ansi('yellowf') + ('Repository #%d does not provide the necessary information: %s' % (i, e)) + ansi('reset'), file=sys.stderr)
            continue
        try:
            repo['url'] = attributes['uri']
            if 'version' in attributes:
                repo['version'] = attributes['version']
        except AttributeError as e:
            print(ansi('yellowf') + ("Repository '%s' does not provide the necessary information: %s" % (path, e)) + ansi('reset'), file=sys.stderr)
            continue
        repos[path] = repo
    return repos


def generate_jobs(repos, args):
    jobs = []
    for path, repo in repos.items():
        path = os.path.join(args.path, path)
        clients = [c for c in vcstool_clients if c.type == repo['type']]
        if not clients:
            from vcstool.clients.none import NoneClient
            job = {
                'client': NoneClient(path),
                'command': None,
                'cwd': path,
                'output': "Repository type '%s' is not supported" % repo['type'],
                'returncode': NotImplemented
            }
            jobs.append(job)
            continue

        client = clients[0](path)
        command = ImportCommand(args, repo['url'], str(repo['version']) if 'version' in repo else None)
        job = {'client': client, 'command': command}
        jobs.append(job)
    return jobs


def add_dependencies(jobs):
    paths = [job['client'].path for job in jobs]
    for job in jobs:
        job['depends'] = set([])
        path = job['client'].path
        while True:
            parent_path = os.path.dirname(path)
            if parent_path == path:
                break
            path = parent_path
            if path in paths:
                job['depends'].add(path)


def main(args=None):
    parser = get_parser()
    add_common_arguments(parser, skip_hide_empty=True, single_path=True, path_help='Base path to clone repositories to')
    args = parser.parse_args(args)
    try:
        repos = get_repositories(args.input)
    except RuntimeError as e:
        print(ansi('redf') + str(e) + ansi('reset'), file=sys.stderr)
        return 1
    jobs = generate_jobs(repos, args)
    add_dependencies(jobs)

    if args.repos:
        output_repositories([job['client'] for job in jobs])

    results = execute_jobs(jobs, show_progress=True, number_of_workers=args.workers, debug_jobs=args.debug)
    output_results(results)

    any_error = any([r['returncode'] != 0 for r in results])
    return 1 if any_error else 0


if __name__ == '__main__':
    sys.exit(main())
