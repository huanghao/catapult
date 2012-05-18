import os

from fabric.api import sudo, run, prompt, abort, local, settings, hide
from fabric.tasks import Task

from state import myenv, load_proj_env

def lpath_exists(path):
    '''
    use this instead of os.path.exists when testing whether local path exists,
    it consider context that set by lcd
    '''
    with settings(hide('warnings'), warn_only=True):
        return local("test -e '%s'" % path).succeeded


def path_exists(path):
    #if files.exists(rel, verbose=True):
    #FIXME: have no idea that why the above command does not work
    #Warning: run() encountered an error (return code 1) while executing 'test -e "$(echo /usr/local/nds/releases/20120510140214)"'
    #run(...., shell=False) will get correct output
    with settings(hide('warnings'), warn_only=True):
        return run("test -e '%s'" % path).succeeded


def mine(*args, **kw):
    #TODO: support myenv in shell running, for sudo,run,etc.
    return sudo(*args, user=myenv.owner, **kw)


def is_owner(path):
    uname = run('uname').stdout
    if uname == 'FreeBSD':
        return mine('id -u').stdout == run("stat -f'%%u' %s" % path).stdout
    else: #if uname == 'Linux':
        return mine('id -u').stdout == run("stat -c'%%u' %s" % path).stdout


def is_python_module(path):
    return path_exists(os.path.join(path, '__init__.py'))


def symlink_python_module(path):
    from distutils import sysconfig
    lib = sysconfig.get_python_lib()
    target = os.path.join(lib, os.path.basename(path))

    if path_exists(target):
        sudo('rm %s' % target)
    sudo('ln -s %s %s' % (path, target))


class ProjTask(Task):
    '''
    base class for project oriented task
    '''
    proj = None

    def set_proj(self, proj):
        self.proj = proj

    def run(self, proj=None, *args, **kw):
        if proj:
            self.set_proj(proj)

        if not self.proj:
            proj = prompt('No project found. Please specify project:')
            if proj:
                self.set_proj(proj)
            else:
                abort('Invalid project name:%s' % proj)

        load_proj_env(self.proj)
        self.work(*args, **kw)

    def work(*args, **kw):
        raise NotImplemented
