import argparse
import sys

from vcstool.streams import set_streams

from .command import Command
from .command import simple_main


class LogCommand(Command):

    command = 'log'
    help = 'Show commit logs'

    def __init__(self, args):
        super(LogCommand, self).__init__(args)
        self.limit = args.limit
        self.limit_tag = args.limit_tag
        self.limit_untagged = args.limit_untagged
        self.verbose = args.verbose


def get_parser():
    parser = argparse.ArgumentParser(
        description='Show commit logs', prog='vcs log')
    group = parser.add_argument_group('"log" command parameters')
    group.add_argument(
        '-l', '--limit', metavar='N', type=int, default=3,
        help='Limit number of logs (0 for unlimited)')
    ex_group = group.add_mutually_exclusive_group()
    ex_group.add_argument(
        '--limit-tag', metavar='TAG',
        help='Limit number of log to the specified tag')
    ex_group.add_argument(
        '--limit-untagged', action='store_true', default=False,
        help='Limit number of log to the last tagged commit')
    group.add_argument(
        '--verbose', action='store_true', default=False,
        help='Show the full commit message')
    return parser


def main(args=None, stdout=None, stderr=None):
    set_streams(stdout=stdout, stderr=stderr)
    parser = get_parser()
    return simple_main(parser, LogCommand, args)


if __name__ == '__main__':
    sys.exit(main())
