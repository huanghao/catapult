import os

from fabric.api import abort, local, cd, runs_once, prompt, run, sudo, env
from fabric.contrib import project
from fabric.tasks import execute

from state import myenv
from ops import mine, ProjTask, mark, svn_revision, relink_current_rel
from timeline import get_local_time, apply_timeline


def get_full_svn_path(ver, svn_type):
    if svn_type == 'ver':
        return os.path.join(myenv.cvs_path, 'tags', ver)
    elif svn_type == 'addr':
        return ver
    else:
        abort('unknown svn_type:%s' % str(svn_type))


class deploy(ProjTask):

    def work(self, ver=None, *args, **kw):
        if 'pre_deploy' in myenv:
            for cmd in myenv.pre_deploy:
                mine(cmd)

        if ver is None:
            ver = prompt('No version found. Please specify version:')
        self.deploy(ver, *args, **kw)

        if 'post_deploy' in myenv:
            for cmd in myenv.post_deploy:
                mine(cmd)

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
        rev = svn_revision(svn)
        mark(workcopy, svn, rev)
        return pid, workcopy

    def upload(self, workcopy):
        with cd(myenv.tmp):
            #FIXME: i think it a bug
            #when calling the upload_project function,
            #must cd to remote target directory,
            #otherwise it will fail to find the uploaded file.

            #TODO: this function will do tar,untar,remove many times in localhost
            project.upload_project(workcopy, myenv.tmp)

    def rearrange_hier(self, pid):
        with cd(myenv.home):
            mine('cp -r %s releases/' % os.path.join(myenv.tmp, pid))
            relink_current_rel('releases/%s' % pid)
            #FIXME: this is a bug, if localhost is one of the remote hosts,
            #workcopy dir and upload target dir are the same
            #and this rm will remove the dir,
            #when comming the second host, deploy will failed to find the workcopy dir
            #sudo('rm -rf %s' % os.path.join(myenv.tmp, pid))


class check(ProjTask):

    def work(self, *args, **kw):
        version_info = self.collect()

        if hasattr(self, 'version_info'):
            if self.version_info != version_info:
                abort('corrupt version. %s(%s) != %s(%s)' \
                    % (self.last_host, self.version_info,
                       env.host, version_info))
        else:
            self.version_info = version_info
            self.last_host = env.host

    def collect(self):
        with cd(os.path.join(myenv.home, 'current')):
            return {
                'TAG': run('cat TAG').stdout,
                'REV': run('cat REV').stdout,
                }


class ideploy(deploy):

    def deploy(self, ver, rev1=None, rev2=None, *args, **kw):
        with cd(myenv.home):
            tag1 = run('cat current/TAG').stdout
            apply_timeline(tag1, ver)
