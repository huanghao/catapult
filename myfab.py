#!/usr/bin/env python
import os
import sys
from getopt import getopt
import subprocess as sp

from fabfile.state import myenv, load_proj_env


def hosts_of_project():
    skip = False
    project_name = None

    for arg in sys.argv[1:]:
        if skip:
            skip = False
            continue
        elif arg.startswith('-'):
            skip = True
            continue
        task_and_params = arg.split(':', 1)
        if len(task_and_params) > 1:
            params = task_and_params[1]
            project_name = params.split(',', 1)[0]

    if not project_name:
        return []

    load_proj_env(project_name)
    return ['-H', ','.join(myenv.hosts)]


def main():
    cwd = os.path.dirname(os.path.abspath(__file__))
    fabfile = os.path.join(cwd, 'fabfile')

    cmd = ['fab',
           '-f', fabfile,
           ]

    cmd.extend(hosts_of_project())
    cmd.extend(sys.argv[1:])

    print cmd
    sp.call(cmd)


if __name__ == '__main__':
    main()
