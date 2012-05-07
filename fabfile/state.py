import os,sys

from fabric.api import env, abort
from fabric.state import _AttributeDict


myenv = env.myenv = _AttributeDict({
    'user': 'mc',
    'workspaces': '/usr/local',
    'ltmp': '/tmp', # local temp path
    'tmp': '/tmp', # remote temp path
})


def install_webadmin_path():
    cwd = os.path.dirname(os.path.abspath(__file__))
    cata_path = os.path.join(cwd, '..')
    sys.path.insert(0, cata_path)

    os.environ['DJANGO_SETTINGS_MODULE'] = 'webadmin.settings'


def load_proj_env(proj):
    install_webadmin_path()

    from webadmin.core.models import Proj
    load_project_fields(Proj.objects.get(name=proj))


def load_project_fields(project):
    myenv.update(((key, getattr(project, key))
       for key in ('name', 'home', 'svn')))

    def split_and_filter(text):
        return filter(None, text.split('\n'))

    myenv.update(((key, split_and_filter(getattr(project, key)))
       for key in ('pre_setup', 'post_setup',
                   'pre_deploy', 'post_deploy',
                   'pre_rollback', 'post_rollback',
                   'link_py_modules',
                   )))
    return
