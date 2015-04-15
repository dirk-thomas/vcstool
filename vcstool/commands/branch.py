import argparse
import sys

from .command import Command, simple_main


class BranchCommand(Command):

    command = 'branch'
    help = 'Show the branches'

    def __init__(self, args):
        super(BranchCommand, self).__init__(args)
        self.all = args.all


def get_parser():
    parser = argparse.ArgumentParser(description='Show the current branch', prog='vcs branch')
    group = parser.add_argument_group('"branch" command parameters')
    group.add_argument('--all', action='store_true', default=False, help='Show all branches')
    return parser


def main(args=None):
    parser = get_parser()
    return simple_main(parser, BranchCommand, args)


if __name__ == '__main__':
    sys.exit(main())
