import argparse
import sys

from vcstool.executor import execute

from .command import add_common_arguments, Command


class PullCommand(Command):

    command = 'pull'
    help = 'Bring changes from the repository into the working copy'

    def __init__(self, args):
        super(PullCommand, self).__init__(args)

    def get_command_line(self, client):
        return client.pull(self)


def get_parser():
    parser = argparse.ArgumentParser(description='Bring changes from the repository into the working copy', prog='vcs pull')
    group = parser.add_argument_group('"pull" command parameters')
    return parser


def main(args=None):
    parser = get_parser()
    add_common_arguments(parser)
    args = parser.parse_args(args)
    cmd = PullCommand(args)
    execute(cmd)
    return 0


if __name__ == '__main__':
    sys.exit(main())
