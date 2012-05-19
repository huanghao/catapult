import os
import sys

from fabric.api import env, abort, runs_once
from fabric.state import _AttributeDict


myenv = env.myenv = _AttributeDict({
    #'ltmp': '/tmp', # local temp path
    'tmp': '/tmp', # remote temp path
})


@runs_once
def install_webadmin_path():
    cwd = os.path.dirname(os.path.abspath(__file__))
    cata_path = os.path.join(cwd, '..')
    sys.path.insert(0, cata_path)

    os.environ['DJANGO_SETTINGS_MODULE'] = 'webadmin.settings'


def update_host(uuid, ips, **info):
    install_webadmin_path()

    from webadmin.core.models import Host, IP
    try:
        host = Host.objects.get(uuid=uuid)
    except Host.DoesNotExist:
        host = Host(uuid=uuid)

    for key, val in info.iteritems():
        if not val or not hasattr(host, key):
            continue
        setattr(host, key, val)
    host.save()
    #FIXME: add transaction
    
    for interface, proto, addr in ips:
        try:
            ip = IP.objects.get(addr=addr)
        except IP.DoesNotExist:
            IP(addr=addr, interface=interface, host=host).save()
        else:
            if not (ip.host == host and ip.interface == interface):
                ip.host = host
                ip.interface = interface
                ip.save()

def load_proj_env(proj):
    install_webadmin_path()

    from webadmin.core.models import Proj
    try:
        load_project_fields(Proj.objects.get(name=proj))
    except Proj.DoesNotExist:
        abort('unknown project:%s' % proj)


def load_project_fields(project):
    myenv.update(((key, getattr(project, key))
       for key in ('name', 'home', 'owner',
                   'cvs_model', 'cvs_path', 'cvs_user', 'cvs_pass',
                   )))

    def split_and_filter(text):
        return filter(None, map(lambda i: i.strip().rstrip('\r'), text.split('\n')))

    myenv.update(((key, split_and_filter(getattr(project, key)))
       for key in ('pre_setup', 'post_setup',
                   'pre_deploy', 'post_deploy',
                   'pre_rollback', 'post_rollback',
                   'link_py_modules',
                   )))

    hosts = [ ip.addr for ip in project.ips.all() ]
    if hosts:
        print 'set env.hosts:', hosts
        env.hosts = hosts
