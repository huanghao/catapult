from fabric.tasks import Task

from state import load_proj_env


class ProjectEnv(Task):
    '''
    load project-ware variables to myenv
    '''
    
    name = 'proj'

    def run(self, project_name):
        load_proj_env(project_name)


