import argparse
import sys

from vcstool.clients import vcstool_clients
from vcstool.commands import vcstool_commands


def get_parser():
    parser = argparse.ArgumentParser(description='Show available commands', prog='vcstool')
    group = parser.add_argument_group('"help" command parameters')
    from vcstool import __version__
    group.add_argument('--clients', action='store_true', default=False, help='Show the available VCS clients')
    group.add_argument('--version', action='version', version='%(prog)s ' + __version__, help='Show the vcstool version')
    return parser


def main(args=None):
    parser = get_parser()
    args = parser.parse_args(args)

    if args.clients:
        print('The available VCS clients are:')
        for client in vcstool_clients:
            print('  %s' % client('.').type)
        return 0

    print('usage: vcs COMMAND [<args>]')
    print('')
    print('The vcs commands are:')
    max_len = max([len(cmd.command) for cmd in vcstool_commands])
    for cmd in vcstool_commands:
        print('  %s%s   %s' % (cmd.command, ' ' * (max_len - len(cmd.command)), cmd.help))
    return 0


if __name__ == '__main__':
    sys.exit(main())
