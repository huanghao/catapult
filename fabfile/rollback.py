from fabric.api import cd, abort

from state import myenv
from ops import mine, get_current_rel, ProjTask, get_prev_rel, relink_current_rel


class rollback(ProjTask):

    def work(self, *args, **kw):
        with cd(myenv.home):
            prev = get_prev_rel()
            if not prev:
                abort('not avaiable previous version')

            curr = get_current_rel()
            if curr == prev:
                abort('loop version link')

            relink_current_rel(prev, False)
            mine('rm -rf %s' % curr)
