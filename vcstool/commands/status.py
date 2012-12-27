import argparse
import sys

from .command import Command, simple_main


class StatusCommand(Command):

    command = 'status'
    help = 'Show the working tree status'

    def __init__(self, args):
        super(StatusCommand, self).__init__(args)
        self.quiet = args.quiet


def get_parser():
    parser = argparse.ArgumentParser(description='Show the working tree status', prog='vcs status')
    group = parser.add_argument_group('"status" command parameters')
    group.add_argument('-q', '--quiet', action='store_true', default=False, help="Don't show unversioned items")
    return parser


def main(args=None):
    parser = get_parser()
    return simple_main(parser, StatusCommand, args)


if __name__ == '__main__':
    sys.exit(main())
