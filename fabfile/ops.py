import os

from fabric.api import sudo, cd, run, prompt, abort, local, lcd
from fabric.tasks import Task
from fabric.contrib import files

from state import myenv, load_proj_env


def mc(*args, **kw):
    #FIXME: change a name
    #TODO: support myenv in shell running, for sudo,run,etc.
    return sudo(*args, user=myenv.user, **kw)


def count_releases():
    with cd(myenv.home):
        n = run('find releases -type d -maxdepth 1 | wc -l').stdout
        return int(n) - 1

        
def get_current_rel():
    with cd(myenv.home):
        return os.path.join(myenv.home, run('readlink current').stdout)


def get_latest_rel():
    with cd(myenv.home):
        return run('ls -At releases | head -n 1').stdout

def relink_current_rel(rel):
    if not os.path.isabs(rel):
        rel = os.path.join(myenv.home, rel)

    if files.exists(rel):
        with cd(myenv.home):
            mc('rm -f current')
            mc('ln -s %s current' % rel)
    else:
        abort('wrong path:%s' % rel)

def is_owner(path):
    return mc('id -u').stdout == run('stat -f"%%u" %s' % path).stdout

def mark(target, tag, rev):
    #TODO: make a deploy chain through a file called "PREV"
    with lcd(target):
        local("echo '%s' > TAG" % tag)
        local("echo '%s' > REV" % rev)

def svn_revision(svn):
    return local("svn info %s | head -n8 | tail -n1 |\
cut -d: -f2 | xargs" % svn, capture=True).stdout




class MyTask(Task):

    def set_name(self, name):
        self.name = name


class ProjTask(MyTask):
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
