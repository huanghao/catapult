from fabric.api import env, run, sudo
from fabric.tasks import Task


class hostinfo(Task):

    def run(self, *args, **kw):
        info = self.parse_dmi()

    def parse_dmi(self):
        dmi = sudo('dmidecode -t system -t processor -t memory').stdout
        print dmi

