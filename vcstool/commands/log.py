import argparse
import sys

from .command import Command, simple_main


class LogCommand(Command):

    command = 'log'
    help = 'Show commit logs'

    def __init__(self, args):
        super(LogCommand, self).__init__(args)
        self.limit = args.limit


def get_parser():
    parser = argparse.ArgumentParser(description='Show commit logs', prog='vcs log')
    group = parser.add_argument_group('"log" command parameters')
    group.add_argument('-l', '--limit', metavar='N', type=int, default=3, help='Limit number of logs')
    return parser


def main(args=None):
    parser = get_parser()
    return simple_main(parser, LogCommand, args)


if __name__ == '__main__':
    sys.exit(main())
