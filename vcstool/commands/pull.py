import argparse
import sys

from vcstool.streams import set_streams

from .command import Command
from .command import simple_main


class PullCommand(Command):

    command = 'pull'
    help = 'Bring changes from the repository into the working copy'

    def __init__(self, args):
        super(PullCommand, self).__init__(args)


def get_parser():
    parser = argparse.ArgumentParser(
        description='Bring changes from the repository into the working copy',
        prog='vcs pull')
    parser.add_argument_group('"pull" command parameters')
    return parser


def main(args=None, stdout=None, stderr=None):
    set_streams(stdout=stdout, stderr=stderr)
    parser = get_parser()
    return simple_main(parser, PullCommand, args)


if __name__ == '__main__':
    sys.exit(main())
