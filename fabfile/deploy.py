import os
import datetime

from fabric.api import abort, cd, runs_once, run, env
from fabric.contrib import project
from fabric.tasks import Task

from state import myenv
import rcs
import schemas


def get_local_time():
    return datetime.datetime.now().strftime('%Y%m%d%H%M%S')


class Deploy(Task):
    '''
    deploy specific version of some project to remote servers
    usage: deploy [ver]
    '''

    name = 'deploy'

    def run(self, ver=None, *args, **kw):
        self.pre()
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

    def deploy(self, ver=None):
        rc = rcs.create(myenv.cvs_model, myenv.cvs_path, ver)
        schema = schemas.Cap(myenv.home)

        pid, workcopy = self.make_workcopy(rc, schema)

        self.upload(schema, workcopy, pid)

        schema.save_current_for_rollback(pid) #TODO: move these two lines to self.work, it's same in ideploy task
        schema.switch_current_to(pid)

    @runs_once #runs_once is incompatible with --parallel
    def make_workcopy(self, rc, schema):
        pid = get_local_time()
        workcopy = os.path.join(myenv.ltmp, pid)

        rc.export(workcopy)
        schema.mark(rc, workcopy)
        return pid, workcopy

    def upload(self, schema, workcopy, pid):
        with cd(myenv.tmp):
            #FIXME: i think it a bug
            #when calling the upload_project function,
            #must cd to remote target directory,
            #otherwise it will fail to find the uploaded file.

            #TODO: this function will do tar,untar,remove many times in localhost
            project.upload_project(workcopy, myenv.tmp)
        schema.copy_to_release(os.path.join(myenv.tmp, pid), pid)
        #FIXME: this is a bug, if localhost is one of the remote hosts,
        #workcopy dir and upload target dir are the same
        #and this rm will remove the dir,
        #when comming the second host, deploy will failed to find the workcopy dir
        #sudo('rm -rf %s' % os.path.join(myenv.tmp, pid))



class Check(Task):
    '''
    check version/revision consistency among project servers
    '''

    name = 'check'

    def run(self, *args, **kw):
        schema = schemas.Cap(myenv.home)

        info = schema.tag_info()
        self.check_same(info)

    def check_same(self, info):
        if not hasattr(self, '_info'):
            self._info = info
        elif self._info != info:
            abort('corrupt version %s on host %s' % (str(info), env.host))


class IncrementalDeploy(Deploy):
    '''
    only checkout the difference between two version, and incrementally deploy to remote servers
    '''

    name = 'ideploy'

    def deploy(self, ver, rev1=None, rev2=None, *args, **kw):
        rc = rcs.create(myenv.cvs_model, myenv.cvs_path, ver, 'ver')
        schema = schemas.Cap(myenv.home)
        ver1 = schema.tag_info()['TAG']

        pid, workcopy, Dfiles = self.make_workcopy(rc, schema, ver1, ver, rev1, rev2)

        self.upload(schema, workcopy, pid)

        schema.save_current_for_rollback(pid)
        schema.remove_useless(pid, Dfiles)
        schema.switch_current_to(pid)

    def upload(self, schema, workcopy, pid):
        with cd(myenv.tmp):
            project.upload_project(workcopy, myenv.tmp)
        schema.overwrite_to_release(os.path.join(myenv.tmp, pid), pid)

    @runs_once
    def make_workcopy(self, rc, schema, ver1, ver2, rev1, rev2):
        pid = get_local_time()
        workcopy = os.path.join(myenv.ltmp, pid)

        Dfiles = rc.iexport(workcopy, ver1, ver2, rev1, rev2)
        schema.mark(rc, workcopy)
        return pid, workcopy, Dfiles
