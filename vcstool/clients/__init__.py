vcstool_clients = []

try:
    from .bzr import BzrClient
    vcstool_clients.append(BzrClient)
except ImportError:
    pass

try:
    from .git import GitClient
    vcstool_clients.append(GitClient)
except ImportError:
    pass

try:
    from .hg import HgClient
    vcstool_clients.append(HgClient)
except ImportError:
    pass

try:
    from .svn import SvnClient
    vcstool_clients.append(SvnClient)
except ImportError:
    pass
