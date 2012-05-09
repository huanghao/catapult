import os
import datetime

from fabric.api import abort, local, cd, lcd, runs_once, prompt, run
from fabric.contrib import project

from state import myenv
from ops import mc, ProjTask
from timeline import get_local_time


def get_full_svn_path(ver, svn_type):
    if svn_type == 'ver':
        return os.path.join(myenv.svn, 'tags', ver)
    elif svn_type == 'addr':
        return ver
    else:
        abort('unknown svn_type:%s' % str(svn_type))


class deploy(ProjTask):

    def work(self, ver=None, *args, **kw):
        if 'pre_deploy' in myenv:
            for cmd in myenv.pre_deploy:
                mc(cmd)

        if ver is None:
            ver = prompt('No version found. Please specify version:')
        self.deploy(ver, *args, **kw)

        if 'post_deploy' in myenv:
            for cmd in myenv.post_deploy:
                mc(cmd)

    def deploy(self, ver, svn_type='ver', *args, **kw):
        '''
        1.export svn tag at local workcopy
        2.put workcopy to remote releases/xxx
        3.remove current symlink
        4.make a new current symlink which refers to dir created in step.2
        '''
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
            rev = local("svn info %s | head -n8 | tail -n1 |\
cut -d: -f2 | xargs" % svn, capture=True).stdout
            local("echo '%s' > REV" % rev)
        return pid, workcopy

    def upload(self, workcopy):
        with cd(myenv.tmp):
            #TODO: this function will do tar,untar,remove many times in localhost
            project.upload_project(workcopy, myenv.tmp)

    def rearrange_hier(self, pid):
        with cd(myenv.home):
            mc('cp -r %s releases/' % os.path.join(myenv.tmp, pid))
            relink_cur_rel('releases/%s' % pid)


from timeline import *

class ideploy(deploy):

    def deploy(self, ver, *args, **kw):
        with cd(myenv.home):
            msg = run('cat current/TAG').stdout
            tag = TagName(msg)
            print tag.full
            print tag.short
            print tag.tag
            
