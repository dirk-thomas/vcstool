import argparse
from multiprocessing import cpu_count
import os

from vcstool.crawler import find_repositories
from vcstool.executor import execute_jobs
from vcstool.executor import generate_jobs
from vcstool.executor import output_repositories
from vcstool.executor import output_results


class Command(object):

    command = None

    def __init__(self, args):
        self.debug = args.debug if 'debug' in args else False
        self.hide_empty = args.hide_empty if 'hide_empty' in args else False
        self.nested = args.nested if 'nested' in args else False
        self.output_repos = args.repos if 'repos' in args else False
        if 'paths' in args:
            self.paths = args.paths
        else:
            self.paths = [args.path]


def check_greater_zero(value):
    try:
        value = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("invalid int value: '%s'" % value)
    if value <= 0:
        raise argparse.ArgumentTypeError(
            "invalid positive int value: '%d'" % value)
    return value


def add_common_arguments(
    parser, skip_hide_empty=False, skip_nested=False, path_nargs='*',
    path_help=None
):
    parser.formatter_class = argparse.ArgumentDefaultsHelpFormatter
    group = parser.add_argument_group('Common parameters')
    group.add_argument(
        '--debug', action='store_true', default=False,
        help='Show debug messages')
    if not skip_hide_empty:
        group.add_argument(
            '-s', '--hide-empty', '--skip-empty', action='store_true',
            default=False, help='Hide repositories with empty output')
    if not skip_nested:
        group.add_argument(
            '-n', '--nested', action='store_true',
            default=False, help='Search for nested repositories')
    try:
        default_workers = cpu_count()
    except NotImplementedError:
        default_workers = 4
    group.add_argument(
        '-w', '--workers', type=check_greater_zero, metavar='N',
        default=default_workers, help='Number of parallel worker threads')
    group.add_argument(
        '--repos', action='store_true', default=False,
        help='List repositories which the command operates on')
    if path_nargs == '?':
        path_help = path_help or 'Base path to look for repositories'
        group.add_argument(
            'path', nargs=path_nargs, type=existing_dir, default=os.curdir,
            help=path_help)
    elif path_nargs == '*':
        path_help = path_help or 'Base paths to look for repositories'
        group.add_argument(
            'paths', nargs=path_nargs, type=existing_dir, default=[os.curdir],
            help=path_help)


def existing_dir(path):
    if not os.path.exists(path):
        raise argparse.ArgumentTypeError("Path '%s' does not exist." % path)
    if not os.path.isdir(path):
        raise argparse.ArgumentTypeError(
            "Path '%s' is not a directory." % path)
    return path


def simple_main(parser, command_class, args=None):
    add_common_arguments(parser)
    args = parser.parse_args(args)

    command = command_class(args)
    clients = find_repositories(command.paths, nested=command.nested)
    if command.output_repos:
        output_repositories(clients)
    jobs = generate_jobs(clients, command)
    results = execute_jobs(
        jobs, show_progress=True, number_of_workers=args.workers,
        debug_jobs=args.debug)

    output_results(results, hide_empty=args.hide_empty)

    any_error = any(r['returncode'] for r in results)
    return 1 if any_error else 0
