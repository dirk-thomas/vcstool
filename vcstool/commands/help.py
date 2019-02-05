from __future__ import print_function

import argparse
import sys

from pkg_resources import load_entry_point
from vcstool.clients import vcstool_clients
from vcstool.commands import vcstool_commands
from vcstool.streams import set_streams


def main(args=None, stdout=None, stderr=None):
    set_streams(stdout=stdout, stderr=stderr)

    # no help to extract command first (which might be followed by --help)
    parser = get_parser(add_help=False)
    ns, _ = parser.parse_known_args(args)

    # help for a specific command
    if ns.command:
        # relay help request foe specific command
        entrypoint = get_entrypoint(ns.command)
        if not entrypoint:
            return 1
        return entrypoint(['--help'])

    # regular parsing validating options and arguments
    parser = get_parser()
    ns = parser.parse_args(args)

    if ns.clients:
        print('The available VCS clients are:')
        for client in vcstool_clients:
            print('  ' + client.type)
        return 0

    if ns.commands:
        print(' '.join([cmd.command for cmd in vcstool_commands]))
        return 0

    # output detailed command list
    parser = get_parser_with_command_only()
    parser.print_help()
    return 0


def get_parser(add_help=True):
    parser = argparse.ArgumentParser(
        prog='vcs', description=_get_description(),
        epilog=_get_epilog(), add_help=add_help)
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        'command', metavar='<command>', nargs='?',
        help='The available commands: ' + ', '.join(
            [cmd.command for cmd in vcstool_commands]))
    group.add_argument(
        '--clients', action='store_true', default=False,
        help='Show the available VCS clients')
    group.add_argument(
        '--commands', action='store_true', default=False,
        help='Output the available commands for auto-completion')
    from vcstool import __version__
    group.add_argument(
        '--version', action='version', version='%(prog)s ' + __version__,
        help='Show the vcstool version')
    return parser


def get_entrypoint(command):
    # accept command with same prefix if unique
    commands = [cmd.command for cmd in vcstool_commands]
    commands = [cmd for cmd in commands if cmd.startswith(command)]
    if len(commands) != 1:
        print(
            "vcs: '%s' is not a vcs command. See 'vcs help'." % command,
            file=sys.stderr)
        if commands:
            print(
                '\nDid you mean one of these?\n' + '\n   '.join(commands),
                file=sys.stderr)
        return None

    return load_entry_point(
        'vcstool', 'console_scripts', 'vcs-' + commands[0])


def get_parser_with_command_only():
    parser = argparse.ArgumentParser(
        prog='vcs', usage='%(prog)s <command>',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='%s\n\n%s' % (
            _get_description(),
            '\n'.join(_get_command_help(vcstool_commands))),
        epilog=_get_epilog(), add_help=False)
    parser.add_argument('command', help=argparse.SUPPRESS)
    return parser


def _get_description():
    return 'Most commands take directory arguments, ' \
        'recursively searching for repositories\n' \
        'in these directories.  ' \
        'If no arguments are supplied to a command, it recurses\n' \
        'on the current directory (inclusive) by default.'


def _get_epilog():
    return "See '%(prog)s <command> --help' for more information " \
        'on a specific command.'


def _get_command_help(commands):
    lines = ['The available commands are:']
    max_len = max(len(cmd.command) for cmd in commands)
    for cmd in vcstool_commands:
        lines.append(
            '   %s%s   %s' %
            (cmd.command, ' ' * (max_len - len(cmd.command)), cmd.help))
    return lines


if __name__ == '__main__':
    sys.exit(main())
