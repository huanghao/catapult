import os

from fabric.api import abort, local, cd, runs_once, prompt, run, sudo, env
from fabric.contrib import project
from fabric.tasks import execute

from state import myenv
from ops import mine, ProjTask, mark, relink_current_rel
from timeline import get_local_time, apply_timeline
import rcs
import schema



class deploy(ProjTask):

    def work(self, ver=None, *args, **kw):
        self.pre()

        if ver is None:
            ver = prompt('No version found. Please specify version:')

        self.deploy(ver, *args, **kw)

        self.post()

    def pre(self):
        if 'pre_deploy' in myenv:
            for cmd in myenv.pre_deploy:
                run(cmd)
    
    def post(self):
        if 'post_deploy' in myenv:
            for cmd in myenv.post_deploy:
                run(cmd)

    def deploy(self, ver, ver_type='ver', *args, **kw):
        rc = rcs.create(myenv.cvs_model, myenv.cvs_path, ver, ver_type)
        pid, workcopy = self.make_workcopy(rc)

        self.upload(workcopy, pid)

        sch = schema.Cap(myenv.home)
        sch.push(pid)
        sch.switch2(pid)

    @runs_once #runs_once is incompatible with --parallel
    def make_workcopy(self, rc):
        pid = get_local_time()
        workcopy = os.path.join(myenv.ltmp, pid)

        local(rc.export(workcopy))
        mark(workcopy, str(rc), rc.rev)
        return pid, workcopy

    def upload(self, workcopy, pid):
        with cd(myenv.tmp):
            #FIXME: i think it a bug
            #when calling the upload_project function,
            #must cd to remote target directory,
            #otherwise it will fail to find the uploaded file.

            #TODO: this function will do tar,untar,remove many times in localhost
            project.upload_project(workcopy, myenv.tmp)
            with cd(myenv.home):
                mine('cp -r %s releases/' % os.path.join(myenv.tmp, pid))
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
