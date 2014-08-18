import argparse
import sys

from .command import Command, simple_main


class LogCommand(Command):

    command = 'log'
    help = 'Show commit logs'

    def __init__(self, args):
        super(LogCommand, self).__init__(args)
        self.limit = args.limit
        self.limit_tag = args.limit_tag
        self.limit_untagged = args.limit_untagged


def get_parser():
    parser = argparse.ArgumentParser(description='Show commit logs', prog='vcs log')
    group = parser.add_argument_group('"log" command parameters')
    ex_group = group.add_mutually_exclusive_group()
    ex_group.add_argument('-l', '--limit', metavar='N', type=int, default=3, help='Limit number of logs (0 for unlimited)')
    ex_group.add_argument('--limit-tag', metavar='TAG', help='Limit number of log to the specified tag')
    ex_group.add_argument('--limit-untagged', action='store_true', default=False, help='Limit number of log to the last tagged commit')
    return parser


def main(args=None):
    parser = get_parser()
    return simple_main(parser, LogCommand, args)


if __name__ == '__main__':
    sys.exit(main())
