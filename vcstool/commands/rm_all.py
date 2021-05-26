
import argparse
import os
from shutil import rmtree
import sys
import urllib.request as request

from vcstool.commands.import_ import file_or_url_type, get_repositories
from vcstool.executor import ansi
from vcstool.streams import set_streams

from .command import Command, existing_dir


class RmAllCommand(Command):
    command = "rm-all"
    help = "Remove the directories indicated by the list of given repositories"

    def __init__(self, *args, **kargs):
        super(RmAllCommand, self).__init__(*args, **kargs)


_cls = RmAllCommand


def get_parser():
    parser = argparse.ArgumentParser(
        description=_cls.help, prog="vcs {}".format(_cls.command))
    group = parser.add_argument_group("Command parameters")
    group.add_argument(
        "--input",
        type=file_or_url_type,
        default="-",
        help="Where to read YAML from",
        metavar="FILE_OR_URL",
    )
    group.add_argument(
        "path",
        nargs="?",
        type=existing_dir,
        default=os.curdir,
        help="Base path to look for repositories",
    )

    group_verification = parser.add_mutually_exclusive_group(required=True)
    group_verification.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        default=False,
        help="Instead of removing, print the paths instead",
    )
    group_verification.add_argument(
        "-f",
        "--force",
        action="store_true",
        default=False,
        help="Force the removal ofthe paths",
    )
    return parser


def main(args=None, stdout=None, stderr=None):
    # CLI Parsing -------------------------------------------------------------
    set_streams(stdout=stdout, stderr=stderr)
    parser = get_parser()
    parser.formatter_class = argparse.ArgumentDefaultsHelpFormatter
    args = parser.parse_args(args)
    try:
        input_ = args.input
        if isinstance(input_, request.Request):
            input_ = request.urlopen(input_)
        repos = get_repositories(input_)
    except (RuntimeError, request.URLError) as e:
        print(ansi("redf") + str(e) + ansi("reset"), file=sys.stderr)
        return 1
    args = vars(args)

    # Get the paths to the repos based on the source and the repo name --------
    paths = [os.path.join(args["path"], rel_path) for rel_path in repos]
    info_str = ansi("yellowf") + str("Paths to delete:") + ansi("reset")
    info_str += "\n\n- "
    info_str += "\n- ".join(paths)
    print(info_str, file=sys.stderr)

    if args["dry_run"]:
        print("\n[Dry Run]", file=sys.stderr)
        return 0

    # Do remove ---------------------------------------------------------------
    for p in paths:
        rmtree(p, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
