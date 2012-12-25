import argparse
import sys

from vcstool.executor import execute

from .command import add_common_arguments, Command


class PushCommand(Command):

    command = 'push'
    help = 'Push changes from the working copy to the repository'

    def __init__(self, args):
        super(PushCommand, self).__init__(args)

    def get_command_line(self, client):
        return client.push(self)


def get_parser():
    parser = argparse.ArgumentParser(description='Push changes from the working copy to the repository', prog='vcs push')
    group = parser.add_argument_group('"push" command parameters')
    return parser


def main(args=None):
    parser = get_parser()
    add_common_arguments(parser)
    args = parser.parse_args(args)
    cmd = PushCommand(args)
    execute(cmd)
    return 0


if __name__ == '__main__':
    sys.exit(main())
