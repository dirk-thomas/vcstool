import argparse
import sys

from vcstool.executor import execute

from .command import add_common_arguments, Command


class LogCommand(Command):

    command = 'log'
    help = 'Show commit logs'

    def __init__(self, args):
        super(LogCommand, self).__init__(args)
        self.limit = args.limit

    def get_command_line(self, client):
        return client.log(self)


def get_parser():
    parser = argparse.ArgumentParser(description='Show commit logs')
    group = parser.add_argument_group('"log" command parameters')
    group.add_argument('-l', '--limit', metavar='N', type=int, default=3, help='Limit number of logs')
    return parser


def main(args=None):
    parser = get_parser()
    add_common_arguments(parser)
    args = parser.parse_args(args)
    cmd = LogCommand(args)
    execute(cmd)
    return 0


if __name__ == '__main__':
    sys.exit(main())
