import os

from fabric.api import abort, cd, runs_once, prompt, run, env
from fabric.contrib import project

from state import myenv
from ops import ProjTask
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
        sch = schema.Cap(myenv.home)

        pid, workcopy = self.make_workcopy(rc, sch)

        self.upload(sch, workcopy, pid)

        sch.save_current_for_rollback(pid)
        sch.switch_current_to(pid)

    @runs_once #runs_once is incompatible with --parallel
    def make_workcopy(self, rc, sch):
        pid = get_local_time()
        workcopy = os.path.join(myenv.ltmp, pid)

        rc.export(workcopy)
        sch.mark(rc, workcopy)
        return pid, workcopy

    def upload(self, sch, workcopy, pid):
        with cd(myenv.tmp):
            #FIXME: i think it a bug
            #when calling the upload_project function,
            #must cd to remote target directory,
            #otherwise it will fail to find the uploaded file.

            #TODO: this function will do tar,untar,remove many times in localhost
            project.upload_project(workcopy, myenv.tmp)
        sch.copy_to_release(os.path.join(myenv.tmp, pid), pid)
        #FIXME: this is a bug, if localhost is one of the remote hosts,
        #workcopy dir and upload target dir are the same
        #and this rm will remove the dir,
        #when comming the second host, deploy will failed to find the workcopy dir
        #sudo('rm -rf %s' % os.path.join(myenv.tmp, pid))


class check(ProjTask):

    def work(self, *args, **kw):
        sch = schema.Cap(myenv.home)

        info = sch.tag_info()
        self.check_same(info)

    def check_same(self, info):
        if not hasattr(self, '_info'):
            self._info = info
        elif self._info != info:
            abort('corrupt version %s on host %s' % (str(info), env.host))


class ideploy(deploy):

    def deploy(self, ver, rev1=None, rev2=None, *args, **kw):
        sch = schema.Cap(myenv.home)
        tag1 = sch.tag_info()['TAG']

        with cd(myenv.home):
            apply_timeline(tag1, ver)
