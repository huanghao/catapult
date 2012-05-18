from fabric.api import settings, sudo, hide, abort, run, env, task
from fabric.tasks import Task, execute

from state import myenv
from cmds import is_owner, path_exists, is_python_module, symlink_python_module, mine
import schemas



class BasicSetup(Task):
    '''
    basic setup, make workspace and build up hierarchical directory structure
    '''

    name = 'basic_setup'

    def run(self):
        self.make_workspace(myenv.home)
        schemas.Cap(myenv.home).build()

    def make_workspace(self, home):
        if path_exists(home):
            if not is_owner(home):
                abort('workspace already exists and does not belong to you, \
make sure you want to reinstall the project:%s' % home)
        else:
            with settings(hide('warnings'), warn_only=True):
                if not sudo('mkdir %s' % home).failed:
                    sudo('chown %s %s' % (myenv.owner, home))



class Setup(BasicSetup):
    '''
    setup for python project, if version assigned, deploy it and link python-module
    usage: setup [ver]
        ver     tag to deploy
    '''

    name = 'setup'

    def run(self, ver=None, *args, **kw):
        self.pre()
        super(Setup, self).run()
        self.post()
        if ver:
            self.deploy_and_link_py(ver, *args, **kw)
    
    def pre(self):
        if 'pre_setup' in myenv:
            for cmd in myenv.pre_setup:
                run(cmd)

    def post(self):
        if 'post_setup' in myenv:
            for cmd in myenv.post_setup:
                run(cmd)

    def deploy_and_link_py(self, ver, *args, **kw):
        bak = env.hosts
        env.hosts = [env.host] #it's tricky

        execute('deploy', ver, *args, **kw)
        self.link_py()

        env.hosts = bak

    def link_py(self):
        for path in myenv.link_py_modules:
            if not is_python_module(path):
                abort("not a python module: %s" % path)

        for path in myenv.link_py_modules:
            symlink_python_module(path)


@task
def rollback():
    '''
    rollback to previous version
    '''
    schema = schemas.Cap(myenv.home)
    curr = schema.current_release()
    prev = schema.get_previous()
    schema.switch_current_to(prev)
    mine("rm -rf '%s'" % curr)


@task
def exterminate():
    '''
    rm project workspace! it is extremely dangous, and it can only be used for testing
    '''
    sudo('rm -rf %s' % myenv.home)
