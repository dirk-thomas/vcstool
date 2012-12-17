import argparse
import sys

from vcstool.executor import execute

from .command import add_common_arguments, Command


class StatusCommand(Command):

    command = 'status'
    help = 'Show the working tree status'

    def __init__(self, args):
        super(StatusCommand, self).__init__(args)
        self.quiet = args.quiet

    def get_command_line(self, client):
        return client.status(self)


def get_parser():
    parser = argparse.ArgumentParser(description='Show the working tree status')
    group = parser.add_argument_group('"status" command parameters')
    group.add_argument('-q', '--quiet', action='store_true', default=False, help="Don't show unversioned items")
    return parser


def main(args=None):
    parser = get_parser()
    add_common_arguments(parser)
    args = parser.parse_args(args)
    cmd = StatusCommand(args)
    execute(cmd)
    return 0


if __name__ == '__main__':
    sys.exit(main())
