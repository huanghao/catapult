from fabric.api import cd, abort

from state import myenv
from ops import mine, count_releases, get_current_rel, get_latest_rel, ProjTask


def check():
    #TODO: check consistency among all hosts, 
    # 1.all the host must in the same version
    # 2.all the host will be rollback to the same version
    pass


class rollback(ProjTask):

    def work(self, *args, **kw):
        '''
        1.remove current release dir
        2.remove the current symlink
        3.make a new current symlink which refers to the latest release dir(sorted by name)
        '''
        with cd(myenv.home):
            n = count_releases()
            if n < 2:
                abort('no previous version to rollback')

            rel = get_current_rel()
            mine('rm -rf %s' % rel)

            latest = get_latest_rel()
            if not latest:
                abort('no latest version for rollback')

            mine('rm -f current')
            mine('ln -s releases/%s current' % latest)
