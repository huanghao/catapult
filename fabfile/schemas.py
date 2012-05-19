import os
import datetime

from fabric.api import settings, abort, lcd, local, cd, runs_once

from cmds import mine, path_exists


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

    @runs_once
    def get_rel_id(self):
        if not hasattr(self, '_rel_id'):
            self._rel_id = self.release(datetime.datetime.now().strftime('%Y%m%d%H%M%S'))
        return self._rel_id

    def push_to_release(self, src):
        rel = self.get_rel_id()
        if path_exists(rel):
            abort('try to overwrite a exists release:%s->%s' % (src, rel))
        mine("cp -r '%s' '%s'" % (src, rel))
        return rel

    def overwrite_to_release(self, src):
        rel = self.get_rel_id()
        if path_exists(rel):
            abort('try to overwrite a exists release:%s->%s' % (src, rel))
        curr = self.current_release(True)
        mine("cp -r '%s' '%s'" % (curr, rel))
        mine("cp -r '%s'/* '%s'" % (src, rel))
        return rel

    def remove_useless(self, Dfiles):
        rel = self.get_rel_id()
        with cd(rel):
            for name in Dfiles:
                mine('rm -rf %s' % name.base)

    def switch_current_to(self, rel=None):
        '''
        switch curernt link to rel.
        if operation failed, leave current link unchanged
        '''
        if rel is None:
            rel = self.get_rel_id()
        path = self.release(rel, True)

        def link_to():
            with settings(warn_only=True):
                return mine('ln -s %s %s' % (path, self.current)).succeeded

        def rollback_if_failed():
            bak = self.current+'.bak'
            mine('mv %s %s' % (self.current, bak))
            def rollback():
                mine('mv %s %s' % (bak, self.current))

            try:
                ok = link_to()
            except:
                rollback()
                raise

            if ok:
                mine('rm -r %s' % bak)
            else:
                rollback()
                abort('switch failed, rollback to original')

        if path_exists(self.current):
            rollback_if_failed()
        else:
            link_to()

    def save_current_for_rollback(self):
        if not path_exists(self.current):
            #for the first time deploy, there is no current link
            return
        path = self.get_rel_id()
        curr = self.current_release()
        mine("echo '%s' > '%s'" % (curr, os.path.join(path, 'PREV')))

    def get_previous(self, rel=None):
        if rel:
            rel = self.release(rel, True)
        else:
            rel = self.current_release(True)
        prev = os.path.join(rel, 'PREV')
        if path_exists(prev):
            return mine("cat '%s'" % prev).stdout
        abort('no avaiable previous version')

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

    def mark(self, rc, target):
        with lcd(target):
            local("echo '%s' > TAG" % rc.path)
            local("echo '%s' > REV" % rc.rev)

    def tag_info(self):
        with cd(self.current):
            return {
                'TAG': mine('cat TAG').stdout,
                'REV': mine('cat REV').stdout,
                }
