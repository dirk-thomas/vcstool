import argparse
import os


class Command(object):

    def __init__(self, args):
        self.debug = args.debug
        self.paths = args.paths
        self.output_repos = args.repos
        for path in self.paths:
            if not os.path.exists(path):
                raise RuntimeError()

    def get_command_line(self, client):
        raise NotImplementedError()


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
