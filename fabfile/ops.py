import os

from fabric.api import sudo, cd, run, prompt, abort, local, lcd, settings, hide
from fabric.tasks import Task
from fabric.contrib import files

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


def count_releases():
    with cd(myenv.home):
        n = run('find releases -type d -maxdepth 1 | wc -l').stdout
        return int(n) - 1

        
def get_current_rel():
    cur = None
    with cd(myenv.home):
        if path_exists('current'):
            cur = os.path.join(myenv.home, run('readlink current').stdout)
    return cur if cur and path_exists(cur) else None


def get_latest_rel():
    with cd(myenv.home):
        return run('ls -At releases | head -n 1').stdout

def relink_current_rel(rel, link_prev=True):
    if not os.path.isabs(rel):
        rel = os.path.join(myenv.home, rel)

    if path_exists(rel):
        if link_prev:
            cur = get_current_rel()
            if cur:
                with cd(rel):
                    mine("echo '%s' > PREV" % cur)

        with cd(myenv.home):
            mine('rm -f current')
            mine('ln -s %s current' % rel)
    else:
        abort('no such path, relink current failed:%s' % rel)


def get_prev_rel():
    prev = None
    with cd(os.path.join(myenv.home, 'current')):
        if path_exists('PREV'):
            prev = run('cat PREV').stdout

    return prev if prev and path_exists(prev) else None


def is_owner(path):
    return mine('id -u').stdout == run("stat -f'%%u' %s" % path).stdout


def mark(target, tag, rev):
    with lcd(target):
        local("echo '%s' > TAG" % tag)
        local("echo '%s' > REV" % rev)

def svn_revision(svn):
    return local("svn info %s | head -n8 | tail -n1 |\
cut -d: -f2 | xargs" % svn, capture=True).stdout


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
