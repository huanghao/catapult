import os,sys

from fabric.api import env, abort
from fabric.state import _AttributeDict


myenv = env.myenv = _AttributeDict({
    'user': 'mc', #FIXME: make this env to project-ware
    'workspaces': '/usr/local',
    'ltmp': '/tmp', # local temp path
    'tmp': '/tmp', # remote temp path
    #FIXME: tmp path need to cleanup automaticly
    #FIXME: workcopy used by "svn export" should be remove automaticly
})


def install_webadmin_path():
    cwd = os.path.dirname(os.path.abspath(__file__))
    cata_path = os.path.join(cwd, '..')
    sys.path.insert(0, cata_path)

    os.environ['DJANGO_SETTINGS_MODULE'] = 'webadmin.settings'


def load_proj_env(proj):
    install_webadmin_path()

    from webadmin.core.models import Proj
    try:
        load_project_fields(Proj.objects.get(name=proj))
    except Proj.DoesNotExist:
        abort('unknown project:%s' % proj)


def load_project_fields(project):
    myenv.update(((key, getattr(project, key))
       for key in ('name', 'home', 'svn')))

    def split_and_filter(text):
        return filter(None, map(lambda i: i.strip().rstrip('\r'), text.split('\n')))

    myenv.update(((key, split_and_filter(getattr(project, key)))
       for key in ('pre_setup', 'post_setup',
                   'pre_deploy', 'post_deploy',
                   'pre_rollback', 'post_rollback',
                   'link_py_modules',
                   )))

    myenv.hosts = [ h.ip for h in project.hosts.all() ]
