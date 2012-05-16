from fabric.api import env
env.shell = '/bin/sh -c '

import setup
import deploy
import rollback
import hostinfo

#TODO: shuold make some install/register mechanism
T = (setup.setup,
     deploy.deploy,
     deploy.ideploy,
     deploy.check,
     rollback.rollback,
     hostinfo.hostinfo,
     )

tasks = [ cls() for cls in T ]
for i, t in enumerate(tasks):
    t.name = t.__class__.__name__
    exec "task_%d = tasks[%d]" % (i, i) #TODO: it's weird
