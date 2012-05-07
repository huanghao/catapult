import os

from fabric.api import settings, sudo, hide, abort
from fabric.tasks import execute
from fabric.contrib import files

from state import myenv, load_proj_env
from ops import mc, is_owner, ProjTask


class basic_setup(ProjTask):

    hier = ['etc',
            'status',
            'releases',
            'run',
            {'log': 'syslog'},
            {'shared': ['log', 'pids', 'system']},
            ]

    def work(self):
        self.make_workspace()
        self.build_hier()

    def make_workspace(self):
        if files.exists(myenv.home) and not is_owner(myenv.home):
            abort('workspace already exists and does not belong to you, make sure you want to reinstall the project:%s' % myenv.home)

        with settings(hide('warnings'), warn_only=True):
            if not sudo('mkdir %s' % myenv.home).failed:
                sudo('chown -R %s %s' % (myenv.user, myenv.home))

    def build_hier(self):
        for path in self.yield_hier():
            mc('mkdir -p %s' % path)

    def yield_hier(self):
        for dname in self.hier:
            if not isinstance(dname, dict):
                yield os.path.join(myenv.home, dname)
            else:
                for parent, childs in dname.items():
                    if hasattr(childs, '__iter__'):
                        for child in childs:
                            yield os.path.join(myenv.home, parent, child)
                    else:
                        yield os.path.join(myenv.home, parent, childs)


def is_python_module(path):
    return files.exists(os.path.join(path, '__init__.py'))


def symlink_python_module(path):
    from distutils import sysconfig
    lib = sysconfig.get_python_lib()
    cmd = 'ln -s %s %s' % \
        (path,
         os.path.join(lib, os.path.basename(path)))
    sudo(cmd)


class pysetup(basic_setup):

    def work(self, ver=None, *args, **kw):
        super(pysetup, self).work()

        if ver:
            execute('deploy', myenv.name, ver, *args, **kw)
            self.link_path()

    def link_path(self):
        for path in myenv.link_py_modules:
            if not is_python_module(path):
                abort("not a python module: %s" % path)

        for path in myenv.link_py_modules:
            symlink_python_module(path)


class setup(pysetup):

    def work(self, *args, **kw):
        if 'pre_setup' in myenv:
            for cmd in myenv.pre_setup:
                mc(cmd)

        super(setup, self).work(*args, **kw)

        if 'post_setup' in myenv:
            for cmd in myenv.post_setup:
                mc(cmd)
