from state import myenv
from ops import mine, ProjTask
import schemas


class rollback(ProjTask):

    def work(self, *args, **kw):
        schema = schemas.Cap(myenv.home)
        curr = schema.current_release()
        prev = schema.get_previous()
        schema.switch_current_to(prev)
        mine("rm -rf '%s'" % curr)
