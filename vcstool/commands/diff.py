import argparse
import sys

from vcstool.executor import execute

from .command import add_common_arguments, Command


class DiffCommand(Command):

    command = 'diff'
    help = 'Show changes in the working tree'

    def __init__(self, args):
        super(DiffCommand, self).__init__(args)
        self.context = args.context

    def get_command_line(self, client):
        return client.diff(self)


def get_parser():
    parser = argparse.ArgumentParser(description='Show changes in the working tree', prog='vcs diff')
    group = parser.add_argument_group('"diff" command parameters')
    group.add_argument('--context', metavar='N', type=int, help='Generate diffs with <n> lines of context')
    return parser


def main(args=None):
    parser = get_parser()
    add_common_arguments(parser)
    args = parser.parse_args(args)
    cmd = DiffCommand(args)
    execute(cmd)
    return 0


if __name__ == '__main__':
    sys.exit(main())
