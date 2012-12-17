import argparse
import sys

from vcstool.executor import execute

from .command import add_common_arguments, Command


class RemotesCommand(Command):

    command = 'remotes'
    help = 'Show the URL of the repository'

    def __init__(self, args):
        super(RemotesCommand, self).__init__(args)

    def get_command_line(self, client):
        return client.remotes(self)


def get_parser():
    parser = argparse.ArgumentParser(description='Show the URL of the repository')
    group = parser.add_argument_group('"remotes" command parameters')
    return parser


def main(args=None):
    parser = get_parser()
    add_common_arguments(parser)
    args = parser.parse_args(args)
    cmd = RemotesCommand(args)
    execute(cmd)
    return 0


if __name__ == '__main__':
    sys.exit(main())
