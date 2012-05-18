from fabric.api import env
env.shell = '/bin/sh -c '
DEBUG = 1


from simple import ProjectEnv
from setup import rollback, Setup
from deploy import Deploy, Check, IncrementalDeploy
from hostinfo import hostinfo
if DEBUG:
    from setup import exterminate

proj_task = ProjectEnv()
setup_task = Setup()
deploy_task = Deploy()
check_task = Check()
ideploy_task = IncrementalDeploy()
