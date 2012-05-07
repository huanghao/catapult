from fabric.api import env
env.shell = '/bin/sh -c'

import setup
import deploy
import rollback

#TODO: shuold make some install/register mechanism
T = (setup.setup,
     deploy.deploy,
     rollback.rollback,
     )

tasks = [ cls() for cls in T ]
for i, t in enumerate(tasks):
    #TODO: it's weird
    t.set_name(t.__class__.__name__)
    exec "task_%d = tasks[%d]" % (i, i)
    
