import argparse
import sys

from .command import Command, simple_main


class BranchCommand(Command):

    command = 'branch'
    help = 'Show the branches'

    def __init__(self, args):
        super(BranchCommand, self).__init__(args)


def get_parser():
    parser = argparse.ArgumentParser(description='Show the branches', prog='vcs branch')
    parser.add_argument_group('"branch" command parameters')
    return parser


def main(args=None):
    parser = get_parser()
    return simple_main(parser, BranchCommand, args)


if __name__ == '__main__':
    sys.exit(main())
