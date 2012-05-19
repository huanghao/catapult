import os
import atexit

from fabric.api import sudo, run, local, settings, hide

from state import myenv


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


class FileCleaner(object):

    def __init__(self):
        self.names = []
        atexit.register(self.clean)

    def __call__(self, name):
        self.names.append(name)

    def clean(self):
        for name in self.names:
            print 'unlink', name
            local("rm -rf '%s'" % name)

unlink = FileCleaner()


