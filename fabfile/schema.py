import os

from fabric.api import settings, abort


from ops import mine, path_exists


class Cap(object):

    hier = ['etc',
            'status',
            'releases',
            'run',
            {'log': 'syslog'},
            {'shared': ['log', 'pids', 'system']},
            ]

    def __init__(self, home):
        assert os.path.isabs(home)
        self.home = home
        self.current = os.path.join(self.home, 'current')

    def current_release(self, check_exists=False):
        '''
        real path to which the current symbol link refer
        '''
        path = mine("readlink '%s'" % self.current).stdout
        if not os.path.isabs(path):
            path = os.path.join(os.path.dirname(self.current), path)
        if check_exists and not path_exists(path):
            abort('no such release:%s' % path)
        return path

    def release(self, rel, check_exists=False):
        if not os.path.isabs(rel):
            rel = os.path.join(self.home, 'releases', rel)

        if check_exists and not path_exists(rel):
            abort('no such release:%s' % rel)
        return rel

    def copy_to_release(self, src, rel):
        rel = self.release(rel)
        if path_exists(rel):
            abort('try to overwrite a exists release:%s->%s' % (src, rel))
        mine("cp -r '%s' '%s'" % (src, rel))

    def switch2(self, rel):
        '''
        switch curernt link to rel.
        if operation failed, leave current link unchanged
        '''
        path = self.release(rel, True)
        bak = self.current+'.bak'

        mine('mv %s %s' % (self.current, bak))
        def rollback():
            mine('mv %s %s' % (bak, self.current))

        try:
            with settings(warn_only=True):
                ok = mine('ln -s %s %s' % (path, self.current)).succeeded
        except:
            rollback()
            raise

        if ok:
            mine('rm -r %s' % bak)
        else:
            rollback()
            abort('switch failed, rollback to original')

    def push(self, rel):
        path = self.release(rel, True)
        curr = self.current_release()
        mine("echo '%s' > '%s'" % (curr, os.path.join(path, 'PREV')))

    def build(self):
        '''
        build hierarchical directory structure in home
        '''
        for path in self.walk():
            mine('mkdir -p %s' % path)

    def walk(self):
        for dname in self.hier:
            if not isinstance(dname, dict):
                yield os.path.join(self.home, dname)
            else:
                for parent, childs in dname.items():
                    if hasattr(childs, '__iter__'):
                        for child in childs:
                            yield os.path.join(self.home, parent, child)
                    else:
                        yield os.path.join(self.home, parent, childs)
