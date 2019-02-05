import argparse
import sys

from vcstool.streams import set_streams

from .command import Command
from .command import simple_main


class DiffCommand(Command):

    command = 'diff'
    help = 'Show changes in the working tree'

    def __init__(self, args):
        super(DiffCommand, self).__init__(args)
        self.context = args.context


def get_parser():
    parser = argparse.ArgumentParser(
        description='Show changes in the working tree', prog='vcs diff')
    group = parser.add_argument_group('"diff" command parameters')
    group.add_argument(
        '--context', metavar='N', type=int,
        help='Generate diffs with <n> lines of context')
    return parser


def main(args=None, stdout=None, stderr=None):
    set_streams(stdout=stdout, stderr=stderr)
    parser = get_parser()
    return simple_main(parser, DiffCommand, args)


if __name__ == '__main__':
    sys.exit(main())
