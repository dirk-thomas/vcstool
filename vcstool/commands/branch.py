import argparse
import sys

from vcstool.executor import execute

from .command import add_common_arguments, Command


class BranchCommand(Command):

    command = 'branch'
    help = 'Show the branches'

    def __init__(self, args):
        super(BranchCommand, self).__init__(args)

    def get_command_line(self, client):
        return client.branch(self)


def get_parser():
    parser = argparse.ArgumentParser(description='Show the branches')
    group = parser.add_argument_group('"branch" command parameters')
    return parser


def main(args=None):
    parser = get_parser()
    add_common_arguments(parser)
    args = parser.parse_args(args)
    cmd = BranchCommand(args)
    execute(cmd)
    return 0


if __name__ == '__main__':
    sys.exit(main())
