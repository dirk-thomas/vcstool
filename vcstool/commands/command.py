import argparse
import os

from vcstool.crawler import find_repositories
from vcstool.executor import execute_jobs, generate_jobs, output_repositories, output_results


class Command(object):

    command = None

    def __init__(self, args):
        self.debug = args.debug if 'debug' in args else False
        self.hide_empty = args.hide_empty if 'hide_empty' in args else False
        self.output_repos = args.repos if 'repos' in args else False
        if 'paths' in args:
            self.paths = args.paths
        else:
            self.paths = [args.path]


def add_common_arguments(parser, skip_hide_empty=False, single_path=False, path_help=None):
    parser.formatter_class = argparse.ArgumentDefaultsHelpFormatter
    group = parser.add_argument_group('Common parameters')
    group.add_argument('--debug', action='store_true', default=False, help='Show debug messages')
    if not skip_hide_empty:
        group.add_argument('-s', '--hide-empty', '--skip-empty', action='store_true', default=False, help='Hide repositories with empty output')
    group.add_argument('-w', '--workers', type=int, metavar='N', default=10, help='Number of parallel worker threads')
    group.add_argument('--repos', action='store_true', default=False, help='List repositories which the command operates on')
    if single_path:
        path_help = path_help or 'Base path to look for repositories'
        group.add_argument('path', nargs='?', type=existing_dir, default=os.curdir, help=path_help)
    else:
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
    results = execute_jobs(jobs, show_progress=True, number_of_workers=args.workers)

    output_results(results, hide_empty=args.hide_empty)

    any_error = any([r['returncode'] != 0 for r in results])
    return 1 if any_error else 0
