import os
import datetime

from fabric.api import task, abort, local, cd, lcd, runs_once, run, prompt
from fabric.contrib import project

from state import myenv, load_proj_env
from ops import mc, ProjTask


def get_local_time():
    return datetime.datetime.now().strftime('%Y%m%d%H%M%S')


def get_full_svn_path(ver, svn_type):
    if svn_type == 'ver':
        return os.path.join(myenv.svn, ver)
    elif svn_type == 'addr':
        return ver
    else:
        abort('unknown svn_type:%s' % str(svn_type))


class deploy(ProjTask):

    def work(self, *args, **kw):
        if 'pre_deploy' in myenv:
            for cmd in myenv.pre_deploy:
                mc(cmd)

        self.deploy(*args, **kw)

        if 'post_deploy' in myenv:
            for cmd in myenv.post_deploy:
                mc(cmd)

    def deploy(self, ver=None, svn_type='ver', *args, **kw):
        '''
        1.export svn tag at local workcopy
        2.put workcopy to remote releases/xxx
        3.remove current symlink
        4.make a new current symlink which refers to dir created in step.2
        '''
        if not ver:
            ver = prompt('No version found. Please specify version:')

        pid, workcopy = self.make_workcopy(ver, svn_type)
        self.upload(workcopy)
        self.rearrange_hier(pid)

    @runs_once #runs_once is incompatible with --parallel
    def make_workcopy(self, ver, svn_type):
        svn = get_full_svn_path(ver, svn_type)

        pid = get_local_time()
        workcopy = os.path.join(myenv.ltmp, pid)

        local('svn export %s %s' % (svn, workcopy))
        with lcd(workcopy):
            local("echo '%s' > TAG" % svn)
            rev = local("svn info %s | head -n5 | tail -n1 | cut -d: -f2 | xargs" % svn).stdout
            local("echo '%s' > REV" % rev) #FIXME! this rev is always empty, i don't know why
        return pid, workcopy

    def upload(self, workcopy):
        with cd(myenv.tmp):
            #TODO: this function will do tar,untar,remove many times in localhost
            project.upload_project(workcopy, myenv.tmp)

    def rearrange_hier(self, pid):
        with cd(myenv.home):
            mc('cp -r %s releases/' % os.path.join(myenv.tmp, pid))
            mc('rm -f current')
            mc('ln -s releases/%s current' % pid)

