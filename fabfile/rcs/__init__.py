import svn

def create(rcs_type, *args, **kw):
    if rcs_type.lower().strip() == 'svn':
        return svn.SVN(*args, **kw)
    abort('unknown rcs type:%s' % rcs_type)
    return None # nerver get to this line
