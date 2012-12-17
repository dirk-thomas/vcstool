from .branch import BranchCommand
from .diff import DiffCommand
from .log import LogCommand
from .pull import PullCommand
from .push import PushCommand
from .remotes import RemotesCommand
from .status import StatusCommand

vcstool_commands = []
vcstool_commands.append(BranchCommand)
vcstool_commands.append(DiffCommand)
vcstool_commands.append(LogCommand)
vcstool_commands.append(PullCommand)
vcstool_commands.append(PushCommand)
vcstool_commands.append(RemotesCommand)
vcstool_commands.append(StatusCommand)
