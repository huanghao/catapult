import os
import tempfile

from fabric.api import abort, runs_once, run, env
from fabric.contrib import project
from fabric.tasks import Task

from state import myenv
from cmds import unlink
import rcs
import schemas


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

        workcopy = self.make_workcopy(rc, schema)
        self.upload(schema, workcopy)

        schema.save_current_for_rollback()
        schema.switch_current_to()

    @runs_once #runs_once is incompatible with --parallel
    def make_workcopy(self, rc, schema):
        workcopy = tempfile.mktemp()
        unlink(workcopy)

        rc.export(workcopy)
        schema.mark(rc, workcopy)
        return workcopy

    def upload(self, schema, workcopy):
        tmpdir = os.path.join(myenv.tmp,
                              os.path.basename(tempfile.mktemp()))
        run("mkdir '%s'" % tmpdir)
        try:
            project.upload_project(workcopy, tmpdir)
            schema.push_to_release(os.path.join(tmpdir,
                os.path.basename(workcopy)))
        finally:
            run("rm -rf '%s'" % tmpdir)


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

        workcopy, Dfiles = self.make_workcopy(rc, schema, ver1, ver, rev1, rev2)

        self.upload(schema, workcopy)

        schema.save_current_for_rollback()
        schema.remove_useless(Dfiles)
        schema.switch_current_to()

    def upload(self, schema, workcopy):
        tmpdir = os.path.join(myenv.tmp,
                              os.path.basename(tempfile.mktemp()))
        run("mkdir '%s'" % tmpdir)
        try:
            project.upload_project(workcopy, tmpdir)
            schema.overwrite_to_release(os.path.join(tmpdir,
                os.path.basename(workcopy)))
        finally:
            run("rm -rf '%s'" % tmpdir)

    @runs_once
    def make_workcopy(self, rc, schema, ver1, ver2, rev1, rev2):
        workcopy = tempfile.mktemp()
        unlink(workcopy)

        Dfiles = rc.iexport(workcopy, ver1, ver2, rev1, rev2)
        schema.mark(rc, workcopy)
        return workcopy, Dfiles
