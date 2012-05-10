#!/usr/local/bin/python
import os
import sys
from getopt import getopt
import subprocess as sp

from fabfile.state import myenv, load_proj_env


def usage():
    print '''usage: %s [options] <project> <command>[:arg2,arg3 ...] [command2 ...] -- [fab options]

Options and arguments:
    -h, --help          this help text
    project             project name that command deal with
    command             fab command
    arg2,arg3 ...       arguments pass to command
                        NOTE: the names start from 2, because the first argument is always the project
    fab options         all command line arguments after '--' will pass to fab without change
''' % os.path.basename(sys.argv[0])


def parse_args():
    opts, args = getopt(sys.argv[1:], 'h', ['--help'])
    for opt, val in opts:
        if opt in ('-h', '--help'):
            usage()
            sys.exit(1)

    if len(args) < 2:
        print >> sys.stderr, 'not enough arguments'
        usage()
        sys.exit(1)

    project = args[0]
    tasks = []
    fab_options = []
    flag = False

    for arg in args[1:]:
        if flag:
            fab_options.append(arg)
        elif arg == '--':
            flag = True
        else:
            tasks.append(arg)

    return project, tasks, fab_options


def get_fab():
    cwd = os.path.dirname(os.path.abspath(__file__))
    fabfile = os.path.join(cwd, 'fabfile')
    return ['fab',
            '-f', fabfile,
            ]

def get_hosts(project):
    load_proj_env(project)
    return myenv.hosts


def push_arg(project, tasks):
    new_tasks = []
    for task in tasks:
        name, left = (task.split(':', 1)+[''])[:2]
        if left:
            arguments = '%s:%s,%s' % (name, project, left)
        else:
            arguments = '%s:%s' % (name, project)
        new_tasks.append(arguments)
    return new_tasks


def main():
    project, tasks, fab_options = parse_args()

    args = push_arg(project, tasks)
    hosts = get_hosts(project)
    cmd = get_fab()

    cmd.extend(['-H', ','.join(hosts)])
    cmd.extend(fab_options)
    cmd.extend(args)

    print ' '.join(cmd)
    sp.call(cmd)


if __name__ == '__main__':
    main()
