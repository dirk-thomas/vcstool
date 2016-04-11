import os
try:
    from queue import Empty, Queue
except ImportError:
    from Queue import Empty, Queue
import sys
import threading
import traceback


def output_repositories(clients):
    ordered_clients = dict((client.path, client) for client in clients)
    for k in sorted(ordered_clients.keys()):
        client = ordered_clients[k]
        print('%s (%s)' % (k, client.__class__.type))


def generate_jobs(clients, command):
    jobs = []
    realpaths = {}
    for client in clients:
        # check if client is a duplicate of another path
        realpath = os.path.realpath(client.path)
        if realpath not in realpaths:
            realpaths[realpath] = [client.path]
        else:
            # override command on client to ignore multiple invocation on same repository
            duplicate_path = realpaths[realpath][0]
            realpaths[realpath].append(client.path)
            method_name = command.__class__.command
            method = getattr(client, method_name, None)
            if method is not None:
                setattr(client, method_name, DuplicateCommandHandler(client, duplicate_path))

        job = {'client': client, 'command': command}
        jobs.append(job)
    return jobs


class DuplicateCommandHandler(object):
    def __init__(self, client, duplicate_path):
        self.client = client
        self.duplicate_path = duplicate_path

    def __call__(self, _command):
        return {
            'cmd': '',
            'cwd': self.client.path,
            'output': "Same repository as '%s'" % self.duplicate_path,
            'returncode': NotImplemented
        }


def execute_jobs(jobs, show_progress=False, number_of_workers=10):
    results = []

    job_queue = Queue()
    result_queue = Queue()

    # create worker threads
    workers = []
    for _ in range(min(number_of_workers, len(jobs))):
        worker = Worker(job_queue, result_queue)
        workers.append(worker)

    # fill job_queue
    for job in jobs:
        job_queue.put(job)

    # start all workers
    [w.start() for w in workers]

    # collect results
    while len(results) < len(jobs):
        (job, result) = result_queue.get()
        if show_progress and len(jobs) > 1:
            if result['returncode'] == NotImplemented:
                sys.stdout.write('s')
            elif result['returncode']:
                sys.stdout.write('E')
            else:
                sys.stdout.write('.')
            sys.stdout.flush()
        result.update(job)
        results.append(result)
    if show_progress and len(jobs) > 1:
        print('')  # finish progress line

    # join all workers
    [w.join() for w in workers]
    return results


class Worker(threading.Thread):

    def __init__(self, job_queue, result_queue):
        super(Worker, self).__init__()
        self.daemon = True
        self.job_queue = job_queue
        self.result_queue = result_queue

    def run(self):
        # process all incoming jobs
        while self.job_queue.qsize():
            try:
                # fetch next job
                job = self.job_queue.get(block=False)
                # process job
                result = self.process_job(job)
                # send result
                self.result_queue.put((job, result))
            except Empty:
                break

    def process_job(self, job):
        command = job['command']
        if not command:
            return {
                'cmd': '',
                'output': job['output'],
                'returncode': 1
            }
        method_name = command.__class__.command
        try:
            method = getattr(job['client'], method_name, None)
            if method is None:
                return {
                    'cmd': '%s.%s(%s)' % (job['client'].__class__.type, method_name, job['command'].__class__.command),
                    'output': "Command '%s' not implemented for client '%s'" % (job['command'].__class__.command, job['client'].__class__.type),
                    'returncode': NotImplemented
                }
            return method(job['command'])
        except Exception as e:
            exc_tb = sys.exc_info()[2]
            filename, lineno, _, _ = traceback.extract_tb(exc_tb)[-1]
            return {
                'cmd': '%s.%s(%s)' % (job['client'].__class__.type, method_name, job['command'].__class__.command),
                'output': "Invocation of command '%s' on client '%s' failed: %s: %s (%s:%s)" % (job['command'].__class__.command, job['client'].__class__.type, type(e).__name__, e, filename, lineno),
                'returncode': 1
            }


def output_result(result, hide_empty=False):
    output = result['output']
    if result['returncode'] == NotImplemented:
        output = ansi('yellowf') + output + ansi('reset')
    elif result['returncode']:
        if not output:
            output = 'Failed with return code %d' % result['returncode']
        output = ansi('redf') + output + ansi('reset')
    elif not result['cmd']:
        output = ansi('yellowf') + output + ansi('reset')
    if output or not hide_empty:
        client = result['client']
        print(ansi('bluef') + '=== ' + ansi('boldon') + client.path + ansi('boldoff') + ' (' + client.__class__.type + ') ===' + ansi('reset'))
    if output:
        try:
            print(output)
        except UnicodeEncodeError:
            print(output.encode(sys.getdefaultencoding(), 'replace'))


def output_results(results, output_handler=output_result, hide_empty=False):
    # output results in alphabetic order
    path_to_idx = {result['client'].path: i for i, result in enumerate(results)}
    idxs_in_order = [path_to_idx[path] for path in sorted(path_to_idx.keys())]
    for i in idxs_in_order:
        output_handler(results[i], hide_empty=hide_empty)


USE_COLOR = hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()
# disable color on Windows except if ConEmuANSI is explicitly enabled
if os.name == 'nt' and os.environ.get('ConEmuANSI', None) != 'ON':
    USE_COLOR = False


def ansi(keyword):
    if not USE_COLOR:
        return ''
    codes = {
        'bluef': '\033[34m',
        'boldon': '\033[1m',
        'boldoff': '\033[22m',
        'cyanf': '\033[36m',
        'redf': '\033[31m',
        'reset': '\033[0m',
        'yellowf': '\033[33m',
    }
    if keyword in codes:
        return codes[keyword]
    return ''
