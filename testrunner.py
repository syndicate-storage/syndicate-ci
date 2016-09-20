#!/usr/bin/env python
# testrunner.py
# loads a yaml file, runs tests defined within that file

import argparse
import collections
import datetime
import itertools
import logging
import os
import pprint
import random
import re
import shlex
import signal
import subprocess
import sys
import tempfile
import threading
import time
import yaml

# logging
log_level = logging.ERROR

logging.basicConfig(level=log_level,
                    format='%(asctime)s.%(msecs)03d | %(levelname)s | %(message)s',
                    datefmt="%Y-%m-%dT%H:%M:%S")

logging.Formatter.converter = time.gmtime

logger = logging.getLogger()

# globals
global args
global r_vars  # replacement vars


def parse_args():

    global args

    parser = argparse.ArgumentParser()

    parser.add_argument('tasks_file',
                        type=argparse.FileType('r'),
                        help="YAML tasks input filename")

    parser.add_argument('output_file',
                        type=argparse.FileType('w'),
                        help="muxed output/error filename")

    parser.add_argument('-d', '--debug',
                        action="store_true",
                        help="print debugging info")

    parser.add_argument('-i', '--immediate',
                        action="store_true",
                        help="immediately print subprocess stdout/err")

    parser.add_argument('-t', '--tap_file',
                        help="TAP output filename")

    parser.add_argument('-f', '--time_format',
                        default="%Y-%m-%dT%H:%M:%S.%f",
                        help="specify a strftime() format")

    args = parser.parse_args()


def import_env():

    global r_vars

    r_vars = {}

    env_var_names = [
        "SYNDICATE_ADMIN",
        "SYNDICATE_MS",
        "SYNDICATE_MS_ROOT",
        "SYNDICATE_MS_KEYDIR",
        "SYNDICATE_PRIVKEY_PATH",
        "SYNDICATE_ROOT",
        "SYNDICATE_TOOL",
        "SYNDICATE_RG_ROOT",
        "SYNDICATE_UG_ROOT",
        "SYNDICATE_AG_ROOT",
        "SYNDICATE_PYTHON_ROOT",
    ]

    logger.debug("Environmental Vars:")

    for e_key in env_var_names:
        r_vars[e_key] = os.environ[e_key]
        logger.debug(" %s=%s" % (e_key, r_vars[e_key]))


def tmpdir(name, varname=None):

    global r_vars

    testprefix = "synd-" + name + "-"
    testdir = tempfile.mkdtemp(dir="/tmp", prefix=testprefix)

    if varname is None:
        varname = name
    r_vars[varname] = testdir

    logger.debug("Created tmpdir '%s', with path: '%s'" % (varname, testdir))


def randfile(parent, name, size=4096, varname=None):

    global r_vars

    if parent not in r_vars:
        logger.error("Unknown parent directory '%s' for file '%s'" %
                     (parent, name))
        sys.exit(1)

    if not os.path.isdir(r_vars[parent]):
        logger.error("Parent '%s' is not a directory for file '%s'" %
                     (r_vars[parent], name))
        sys.exit(1)

    path = r_vars[parent] + "/" + name

    r_file = open(path, 'w')

    pattern = list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
    randstring = "".join([random.choice(pattern) for _ in range(size)])

    r_file.write(randstring)
    r_file.close()

    if varname is None:
        varname = name
    r_vars[varname] = path

    logger.debug("Created randfile '%s' at '%s' of size %d" % (varname, path, size))


def randname(name, size=12, varname=None):

    global r_vars

    pattern = list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
    r_name = "%s-%s" % (name, "".join([random.choice(pattern) for _ in range(size)]))

    if varname is None:
        varname = name
    r_vars[varname] = r_name

    logger.debug("Created randname '%s' with value '%s'" % (varname, r_name))


def newvar(name, value):

    global r_vars

    rv = re.compile('\$(\w+)')  # capture just the variable

    rv_matches = rv.findall(value)
    for match in rv_matches:
        if match in r_vars:
            rr = re.compile('\$%s' % match)
            value = rr.sub(r_vars[match], value, count=1)
        else:
            logger.error("Unknown variable: '$%s' when creating newvar '%s'" %
                         (match, name))

    r_vars[name] = value

    logger.debug("Created newvar '%s' with value '%s'" % (name, value))


class CommandRunner():
    """
    Encapsulates running a subprocess and validates return code and optionally
    stdout/err streams
    """

    def __init__(self, cmd_desc, taskb_name):

        self.c = {}
        self.p = {}
        self.out_th = {}
        self.err_th = {}
        self.start_t = None
        self.end_t = None

        self.taskb_name = taskb_name
        self.q = collections.deque()

        for req_key in ["name", "command", ]:
            if req_key not in cmd_desc:
                logger.error("no key '%s' in command description: %s" %
                             (req_key, cmd_desc))
                sys.exit(1)

        self.c = cmd_desc

    def __pipe_reader(self, stream, stream_name, task_desc):

        global args

        for line in iter(stream.readline, b''):
            event = {"time": time.time(), "stream": stream_name,
                     "task": task_desc, "line": line}
            self.q.append(event)

            # print is not thread safe, but works, mostly...
            if args.immediate:
                print self.decorate_output(event)

        stream.close()

        self.end_t = time.time()

    @staticmethod
    def decorate_output(event):

        global args

        event_dt = datetime.datetime.utcfromtimestamp(event['time'])

        return ('%s | %s,%s | %s' % (event_dt.strftime(args.time_format),
                event['task'], event['stream'],
                event['line'].rstrip()))

    def run(self):

        global r_vars

        command = self.c['command']

        # replace variables
        rv = re.compile('\$(\w+)')  # capture just the variable

        rv_matches = rv.findall(command)
        for match in rv_matches:
            if match in r_vars:
                rr = re.compile('\$%s' % match)
                command = rr.sub(r_vars[match], command, count=1)
            else:
                logger.error("Task '%s' has unknown variable: '$%s'" %
                             (self.c['name'], match))

        logger.debug("Running Task '%s': `%s`" % (self.c['name'], command))

        # split command into array
        c_array = shlex.split(command)

        ON_POSIX = 'posix' in sys.builtin_module_names
        self.p = subprocess.Popen(c_array, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, bufsize=1,
                                  close_fds=ON_POSIX)

        self.start_t = time.time()

        self.out_th = threading.Thread(
                        target=self.__pipe_reader,
                        args=(self.p.stdout, "o",
                              "%s:%s" % (self.taskb_name, self.c['name'])))

        self.out_th.daemon = True  # thread ends when subprocess does
        self.out_th.start()

        self.err_th = threading.Thread(
                        target=self.__pipe_reader,
                        args=(self.p.stderr, "e",
                              "%s:%s" % (self.taskb_name, self.c['name'])))

        self.err_th.daemon = True
        self.err_th.start()

    def terminate(self):

        # check to see if already exited, send terminate signal otherwise
        retcode = self.p.poll()

        if retcode is not None:
            logger.debug("Task '%s' already terminated, returncode %d" %
                         (self.c['name'], retcode))
        else:
            logger.debug("Terminating task '%s'" % self.c['name'])
            self.p.terminate()

            # returncode likely negative of signal, only set if not set
            if 'returncode' not in self.c:
                self.c['returncode'] = - signal.SIGTERM

    def send_signal(self, signal):

        logger.debug("Sending signal '%d' to task '%s'" %
                     (signal, self.c['name']))

        self.p.send_signal(signal)

        # returncode is likely negative of signal, only set if not set
        if 'returncode' not in self.c:
            self.c['returncode'] = - signal

    def duration(self, multiplier=1):

        # multiplier is to easily generate mili/micro-seconds
        if self.end_t is not None:
            return (self.end_t - self.start_t) * multiplier
        else:
            return None

    def finish(self, tap_writer):

        failures = []

        self.out_th.join()
        self.err_th.join()
        self.p.wait()

        logger.debug("Duration of task '%s': %.6f" %
                     (self.c['name'], self.duration()))

        # default is 0, check against this in any case
        returncode = 0

        if 'returncode' in self.c:
            returncode = self.c['returncode']

        if self.p.returncode == returncode:
            logger.debug("Task '%s' exited correctly: %s" %
                         (self.c['name'], self.p.returncode))
        else:
            retcode_fail = ("Task '%s' incorrect exit: %s, expecting %s" %
                            (self.c['name'], self.p.returncode, returncode))
            logger.error(retcode_fail)
            failures.append(retcode_fail)

        stdout_str = ""
        stderr_str = ""

        for dq_item in self.q:
            if dq_item['stream'] == "o":
                stdout_str += dq_item['line']
            elif dq_item['stream'] == "e":
                stderr_str += dq_item['line']
            else:
                raise Exception("Unknown stream: %s" % dq_item['stream'])

        # checks against stdout/stderr are optional
        if 'outfile' in self.c:
            if stdout_str == open(self.c['outfile']).read():
                logger.debug("Task '%s' stdout matches contents of %s" %
                             (self.c['name'], self.c['outfile']))
            else:
                outfile_fail = ("Task '%s' stdout does not match contents of %s" %
                                (self.c['name'], self.c['outfile']))
                logger.error(outfile_fail)
                failures.append(outfile_fail)

        if 'errfile' in self.c:
            if stderr_str == open(self.c['errfile']).read():
                logger.debug("Task '%s' stderr matches contents of %s"
                             % (self.c['name'], self.c['errfile']))
            else:
                errfile_fail = ("Task '%s' stderr does not match contents of %s" %
                                (self.c['name'], self.c['errfile']))
                logger.error(errfile_fail)
                failures.append(errfile_fail)

        if tap_writer:

            yaml_data = {"duration_ms": "%.6f" % self.duration(1000)}

            if failures:
                yaml_data["failures"] = failures
                tap_writer.record_test(False, self.c['name'], yaml_data)
            else:
                tap_writer.record_test(True, self.c['name'], yaml_data)

        return {"failures": failures, "q": self.q}


class RunParallel():

    def __init__(self, taskblock, tap_writer=None):

        self.runners = []
        self.run_out = []

        if 'tasks' not in taskblock:
            logger.error("No tasks in taskblock '%s'" % name)
            os.exit(1)

        self.tasks = taskblock['tasks']
        self.taskblock_name = taskblock['name']
        self.tap_writer = tap_writer

    def num_tests(self):
        return len(self.tasks)

    def run(self):
        for task in self.tasks:
            cr = CommandRunner(task, self.taskblock_name)
            self.runners.append({"name": task['name'], "cr": cr})
            cr.run()

        for runner in self.runners:
            self.run_out.append(runner['cr'].finish(self.tap_writer))


class RunSequential(RunParallel):

    def run(self):
        for task in self.tasks:
            cr = CommandRunner(task, self.taskblock_name)
            cr.run()
            self.run_out.append(cr.finish(self.tap_writer))


class RunDaemon(RunParallel):

    def run(self):
        for task in self.tasks:
            cr = CommandRunner(task, self.taskblock_name)
            self.runners.append({"name": task['name'], "cr": cr})
            cr.run()

    def stop(self):
        for runner in self.runners:
            runner['cr'].terminate()
            self.run_out.append(runner['cr'].finish(self.tap_writer))


class TAPWriter():

    def __init__(self, tap_filename):
        """
        generate a TAP file of results
        """

        self.current_test = 0

        self.tap_file = open(tap_filename, 'w')

    def write_header(self, num_tests):

        self.tap_file.write("TAP version 13\n")
        self.tap_file.write("1..%d\n" % num_tests)

    def record_test(self, success, comment="", extra_data=None):

        self.current_test += 1

        suffix = ""

        if comment:
            suffix = " # " + str(comment)

        if success:
            self.tap_file.write("ok %d%s\n" % (self.current_test, suffix))
        else:
            self.tap_file.write("not ok %d%s\n" % (self.current_test, suffix))

        if extra_data:

            # YAML must be indented:
            # http://testanything.org/tap-version-13-specification.html#yaml-blocks

            yaml_str = yaml.dump(extra_data, indent=4,
                                 explicit_start=True, explicit_end=True,
                                 default_flow_style=False).rstrip()

            indented = '\n'.join(
                "  " + line for line in yaml_str.split('\n')) + '\n'

            self.tap_file.write(indented)

    def __del__(self):
        self.tap_file.close()


class TaskBlocksRunner():

    task_blocks = []
    runners = []
    daemons = []
    runb_out = []
    tap_writer = None

    def __init__(self, tasks_filename, tap_filename=""):
        """
        Load the tests file and parse from YAML
        Verify taskblock syntax
        """

        try:
            self.task_blocks = yaml.safe_load(tasks_filename)
        except yaml.YAMLError as exc:
            logger.error("Problem loading input file: " + exc)
            sys.exit(1)

        if tap_filename:
            tap_writer = TAPWriter(tap_filename)

        num_tests = 0

        for taskb in self.task_blocks:

            # validate task blocks from YAML
            for req_key in ["name", "type", ]:
                if req_key not in taskb:
                    logger.error("No '%s' defined in task block: %s" %
                                 (req_key, taskb))
                    sys.exit(1)

            if taskb['type'] not in ["setup", "sequential", "parallel", ]:
                logger.error("Unknown task type '%s' in task block: %s" %
                             (taskb['type'], taskb))
                sys.exit(1)

            # create the task blocks
            if taskb['type'] == "setup":

                if 'tmpdirs' in taskb:
                    for tdir in taskb['tmpdirs']:
                        tmpdir(tdir['name'], tdir['varname'])

                if 'randfiles' in taskb:
                    for rfile in taskb['randfiles']:
                        randfile(rfile['parent'], rfile['name'], rfile['size'])

                if 'randname' in taskb:
                    for r_name in taskb['randnames']:
                        randname(r_name)

                if 'vars' in taskb:
                    for v_name in taskb['vars']:
                        newvar(v_name['name'], v_name['value'])

                if 'tasks' in taskb:
                    daemon_runner = RunDaemon(taskb)
                    self.daemons.append(
                        {"name": taskb['name'], "runner": daemon_runner})

            elif taskb['type'] == "sequential":
                seq_runner = RunSequential(taskb, tap_writer)
                num_tests += seq_runner.num_tests()
                self.runners.append(
                    {"name": taskb['name'], "runner": seq_runner})

            elif taskb['type'] == "parallel":
                par_runner = RunParallel(taskb, tap_writer)
                num_tests += par_runner.num_tests()
                self.runners.append(
                    {"name": taskb['name'], "runner": par_runner})

            else:
                logger.error("Unknown task type '%s' in task block: %s" %
                             (taskb['type'], taskb))
                sys.exit(1)

        tap_writer.write_header(num_tests)

    def start_daemons(self):

        for daemon in self.daemons:
            daemon['runner'].run()

    def run_task_blocks(self):

        for runner in self.runners:
            runner['runner'].run()
            self.runb_out.append(runner['runner'].run_out)

    def stop_daemons(self):

        for daemon in self.daemons:
            daemon['runner'].stop()
            self.runb_out.append(daemon['runner'].run_out)

    def print_timesorted(self, output_file):

        global args

        all_output = itertools.chain()

        for tasks in self.runb_out:
            for task in tasks:
                all_output = itertools.chain(all_output, task['q'])

        sorted_outs = sorted(all_output, key=lambda k: k['time'])

        for dq_item in sorted_outs:
            output_file.write(CommandRunner.decorate_output(dq_item) + "\n")

if __name__ == "__main__":
    parse_args()
    import_env()

    global args

    if args.debug:
        logger.setLevel(logging.DEBUG)

    start_t = time.time()
    start_dt = datetime.datetime.utcfromtimestamp(start_t)
    logger.debug("Started at %s" % start_dt.strftime(args.time_format))

    tbr = TaskBlocksRunner(args.tasks_file, args.tap_file)

    tbr.start_daemons()
    tbr.run_task_blocks()
    tbr.stop_daemons()
    tbr.print_timesorted(args.output_file)

    args.output_file.close()

    end_t = time.time()
    duration = end_t - start_t
    end_dt = datetime.datetime.utcfromtimestamp(end_t)

    logger.debug("Ended at %s, duration: %.6f" %
                 (end_dt.strftime(args.time_format), duration))
