import argparse
import sys

from vcstool.streams import set_streams

from .command import Command
from .command import simple_main


class ReposCommand(Command):

    command = 'repos'
    help = 'Show repository status per line'

    def __init__(self, args):
        super(ReposCommand, self).__init__(args)
        self.quiet = args.quiet


def get_parser():
    parser = argparse.ArgumentParser(
        description='Show repository status per line', prog='vcs repos')
    group = parser.add_argument_group('"repos" command parameters')
    group.add_argument(
        '-q', '--quiet', action='store_true', default=False,
        help="Don't show unversioned items")
    group.add_argument(
        '--wstool_info', action='store_true', default=True,
        help="Show output in wstool info style")
    return parser


def main(args=None, stdout=None, stderr=None):
    set_streams(stdout=stdout, stderr=stderr)
    parser = get_parser()
    return simple_main(parser, ReposCommand, args)


if __name__ == '__main__':
    sys.exit(main())
