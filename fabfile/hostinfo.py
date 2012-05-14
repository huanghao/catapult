from fabric.api import env, run, sudo
from fabric.tasks import Task


class hostinfo(Task):

    def run(self, *args, **kw):
        print env.host
        sudo('dmidecode -t system -t processor -t memory')
        run('df -h')

