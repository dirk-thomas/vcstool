import argparse
import os

from vcstool.crawler import find_repositories
from vcstool.executor import execute_jobs, generate_jobs, output_repositories, output_results


class Command(object):

    command = None

    def __init__(self, args):
        self.debug = args.debug if 'debug' in args else False
        self.output_repos = args.repos if 'repos' in args else False
        self.paths = args.paths


def add_common_arguments(parser):
    group = parser.add_argument_group('Common parameters')
    group.add_argument('--debug', action='store_true', default=False, help='Show debug messages')
    group.add_argument('--repos', action='store_true', default=False, help='List repositories which the command operates on')
    group.add_argument('paths', nargs='*', type=existing_dir, default=[os.curdir], help='Base paths to look for repositories')


def existing_dir(path):
    if not os.path.exists(path):
        raise argparse.ArgumentTypeError("Path '%s' does not exist." % path)
    if not os.path.isdir(path):
        raise argparse.ArgumentTypeError("Path '%s' is not a directory." % path)
    return path


def simple_main(parser, command_class, args=None):
    add_common_arguments(parser)
    args = parser.parse_args(args)

    command = command_class(args)
    clients = find_repositories(command.paths)
    if command.output_repos:
        output_repositories(clients)
    jobs = generate_jobs(clients, command)
    results = execute_jobs(jobs, show_progress=True)

    output_results(results)
    return 0
