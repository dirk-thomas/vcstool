import os
try:
    import queue
except ImportError:
    import Queue as queue
import subprocess
import sys
import threading


def output_repositories(clients):
    ordered_clients = dict((client.path, client) for client in clients)
    for k in sorted(ordered_clients.keys()):
        client = ordered_clients[k]
        print('%s (%s)' % (k, client.__class__.type))


def generate_jobs(clients, command):
    jobs = []
    for client in clients:
        job = {'client': client, 'command': command}
        jobs.append(job)
    return jobs


def execute_jobs(jobs, show_commands=False, show_progress=False):
    results = []

    job_queue = queue.Queue()
    result_queue = queue.Queue()

    # create worker threads
    workers = []
    for _ in range(min(10, len(jobs))):
        worker = Worker(job_queue, result_queue)
        workers.append(worker)

    # fill job_queue
    for job in jobs:
        job_queue.put(job)

    # start all workers
    _ = [w.start() for w in workers]

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
    _ = [w.join() for w in workers]
    return results


class Worker(threading.Thread):

    def __init__(self, job_queue, result_queue):
        super(Worker, self).__init__()
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
            except queue.Empty:
                break

    def process_job(self, job):
        method_name = job['command'].__class__.command
        try:
            method = getattr(job['client'], method_name)
            return method(job['command'])
        except AttributeError as e:
            return {
                'cmd': '%s.%s(%s)' % (job['client'].__class__.type, method_name, job['command'].__class__.command),
                'output': "Command '%s' not implemented for client '%s'" % (job['command'].__class__.command, job['client'].__class__.type),
                'returncode': NotImplemented
            }
        except Exception as e:
            return {
                'cmd': '%s.%s(%s)' % (job['client'].__class__.type, method_name, job['command'].__class__.command),
                'output': "Invocation of command '%s' on client '%s' failed: %s" % (job['command'].__class__.command, job['client'].__class__.type, e),
                'returncode': 1
            }


def output_result(result):
    client = result['client']
    print(ansi('bluef') + '=== ' + ansi('boldon') + client.path + ansi('boldoff') + ' (' + client.__class__.type + ') ===' + ansi('reset'))
    output = result['output'].rstrip()
    if result['returncode'] == NotImplemented:
        output = ansi('yellowf') + output + ansi('reset')
    elif result['returncode']:
        if not output:
            output = 'Failed with return code %d' % result['returncode']
        output = ansi('redf') + output + ansi('reset')
    elif not result['cmd']:
        output = ansi('yellowf') + output + ansi('reset')
    if output:
        print(output)


def output_results(results, output_handler=output_result):
    # output results in alphabetic order
    path_to_idx = {result['client'].path: i for i, result in enumerate(results)}
    idxs_in_order = [path_to_idx[path] for path in sorted(path_to_idx.keys())]
    for i in idxs_in_order:
        output_handler(results[i])


def ansi(keyword):
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
