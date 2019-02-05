import argparse
import sys

from vcstool.streams import set_streams

from .command import Command
from .command import simple_main


class RemotesCommand(Command):

    command = 'remotes'
    help = 'Show the URL of the repository'

    def __init__(self, args):
        super(RemotesCommand, self).__init__(args)


def get_parser():
    parser = argparse.ArgumentParser(
        description='Show the URL of the repository', prog='vcs remotes')
    parser.add_argument_group('"remotes" command parameters')
    return parser


def main(args=None, stdout=None, stderr=None):
    set_streams(stdout=stdout, stderr=stderr)
    parser = get_parser()
    return simple_main(parser, RemotesCommand, args)


if __name__ == '__main__':
    sys.exit(main())
