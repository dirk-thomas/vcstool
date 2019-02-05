from __future__ import print_function

import sys

from vcstool.commands.help import get_entrypoint
from vcstool.commands.help import get_parser
from vcstool.commands.help import main as help_main
from vcstool.streams import set_streams


def main(args=None, stdout=None, stderr=None):
    set_streams(stdout=stdout, stderr=stderr)

    # no help to extract command first (which might be followed by --help)
    parser = get_parser(add_help=False)
    ns, _ = parser.parse_known_args(args)
    args = args if args is not None else sys.argv[1:]

    # relay to specific command
    if ns.command and ns.command != 'help':
        entrypoint = get_entrypoint(ns.command)
        if not entrypoint:
            return 1

        args.remove(ns.command)
        return entrypoint(args)

    # remove help command if specified
    if ns.command:
        args.remove(ns.command)

    return help_main(args)


if __name__ == '__main__':
    sys.exit(main())
