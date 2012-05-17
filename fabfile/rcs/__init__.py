from fabric.api import abort

import svn
import git


def create(rcs_type, *args, **kw):
    type_ = rcs_type.lower().strip()
    if type_ == 'svn':
        return svn.SVN(*args, **kw)
    elif type_ == 'git':
        return git.Git(*args, **kw)
    abort('unknown rcs type:%s' % rcs_type)
    return None # nerver get to this line
