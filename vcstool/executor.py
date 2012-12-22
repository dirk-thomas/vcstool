import os
import subprocess
import sys

from .crawler import find_repositories


def execute(command):
    # determine repositories
    clients = find_repositories(command.path)
    if command.repos:
        ordered_clients = dict((client.path, client) for client in clients)
        for k in sorted(ordered_clients.keys()):
            client = ordered_clients[k]
            print('%s (%s)' % (k, client.type))

    jobs = {}
    for client in clients:
        # generate command line
        cmd = command.get_command_line(client)
        job = {'client': client, 'cmd': cmd}
        if not cmd:
            cmd = ['echo', '"%s" is not implemented for client "%s"' % (command.__class__.__name__, client.type)]
        if command.debug:
            print('Executing shell command "%s" in "%s"' % (' '.join(cmd), client.path))
        # execute command line
        p = subprocess.Popen(cmd, shell=False, cwd=os.path.abspath(client.path), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        job['process'] = p
        jobs[p.pid] = job

    # wait for all jobs to finish
    wait_for = jobs.keys()
    while wait_for:
        # wait for any/next process
        try:  # if os.name == 'posix':
            pid, retcode = os.wait()
        except AttributeError:
            pid, retcode = os.waitpid(wait_for[0], 0)
        # collect retcode and output
        if pid in wait_for:
            wait_for.remove(pid)
            job = jobs[pid]
            job['retcode'] = retcode
            job['stdout'] = job['process'].stdout.read()
            # indicate progress
            if len(jobs) > 1:
                if job['cmd']:
                    if retcode == 0:
                        sys.stdout.write('.')
                    else:
                        sys.stdout.write('E')
                else:
                    sys.stdout.write('s')
                sys.stdout.flush()
    if len(jobs) > 1:
        print('')  # finish progress line

    # output results in alphabetic order
    path_to_pid = {job['client'].path: pid for pid, job in jobs.items()}
    pids_in_order = [path_to_pid[path] for path in sorted(path_to_pid.keys())]
    for pid in pids_in_order:
        job = jobs[pid]
        client = job['client']
        print(ansi('bluef') + '=== ' + ansi('boldon') + client.path + ansi('boldoff') + ' (' + client.type + ') ===' + ansi('reset'))
        output = job['stdout'].rstrip()
        if job['retcode'] != 0:
            if not output:
                output = 'Failed with retcode %d' % job['retcode']
            output = ansi('redf') + output + ansi('reset')
        elif not job['cmd']:
            output = ansi('yellowf') + output + ansi('reset')
        if output:
            print(output)


def ansi(keyword):
    codes = {
        'bluef': '\033[34m',
        'boldon': '\033[1m',
        'boldoff': '\033[22m',
        'redf': '\033[31m',
        'reset': '\033[0m',
        'yellowf': '\033[33m',
    }
    if keyword in codes:
        return codes[keyword]
    return ''
