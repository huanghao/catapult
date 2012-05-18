import os

from fabric.api import abort, local, lcd

from ..cmds import lpath_exists
from ..state import myenv


class SmartName(object):

    def __init__(self, full_path_or_repo, tag=None, base=None):
        fpor = full_path_or_repo
        if tag is not None and base is not None:
            self.repo = fpor
            self.tag = tag
            self.base = base
        elif self.is_svn_url(fpor):
            self.repo, left = fpor.split('/tags/', 1)
            self.tag, self.base = (left.split('/', 1)+[''])[:2]
        else:
            self.repo = myenv.cvs_path
            self.tag, self.base = (fpor.split('/', 1)+[''])[:2]

    @property
    def dirname(self):
        return os.path.dirname(self.base)

    def is_svn_url(self, path):
        return '://' in path

    def spawn(self, tag):
        return SmartName(self.repo, tag, self.base)

    def __str__(self):
        return os.path.join(self.repo, 'tags', self.tag, self.base)

    def __eq__(self, r):
        return str(self) == str(r)

    def __ne__(self, r):
        return not self == r

    def __lt__(self, r):
        return str(self) < str(r)

    def __le__(self, r):
        return (self == r) or (self < r)

    def __gt__(self, r):
        return str(self) > r

    def __ge__(self, r):
        return (self == r) or (self > r)



class SVN(object):

    def __init__(self, base, version, version_type='ver'):
        self.path, self.version = self.make_full_path(base, version, version_type)

    def make_full_path(self, base, version, version_type):
        if version_type == 'ver':
            if version is None:
                return os.path.join(base, 'trunk'), 'trunk'
            else:
                return os.path.join(base, 'tags', version), version
        elif version_type == 'path':
            return version, os.path.basename(version.rstrip('/'))
        abort('unknown version_type:%s' % str(version_type))

    def export(self, target):
        local("svn export '%s' '%s'" % (self.path, target))

    def query_revision(self):
        return local("svn info %s | head -n8 | tail -n1 |\
cut -d: -f2 | xargs" % self.path, capture=True).stdout.strip()

    @property
    def ver(self):
        return self.version

    @property
    def rev(self):
        if not hasattr(self, '_rev'):
            self._rev = self.query_revision()
        return self._rev

    def __str__(self):
        return self.path

    def diff(self, old, new, rev1, rev2):
        if old == new and rev1 == rev2:
            abort('can not deploy a duplicated (version,revision):(%s,%s)' \
                      % (new.tag, rev1))

        cmd = ['svn diff --summarize',
               '--old=' + str(old),
               '--new=' + str(new),
               ]
        if rev1 and rev2:
            cmd.append('-r%s:%s' % (rev1, rev2))

        svnlog = local(' '.join(cmd), capture=True).stdout.strip()
        if not svnlog:
            abort('no diff between two (version,revision):(%s,%s)(%s,%s)' \
                      % (old.tag, new.tag, rev1, rev2))

        print 'CHANGE HISTORY:'
        print svnlog
        print '-'*10
        return svnlog

    def MAD(self, svnlog):
        def parse():
            for line in svnlog.split('\n'):
                action, path = line.split()
                yield action, SmartName(path)

        Dfiles = []
        MAfiles = []
        for action, path in parse():
            if action == 'D':
                Dfiles.append(path)
            else:
                MAfiles.append(path)
        return MAfiles, Dfiles

    def iexport(self, target, ver1, ver2, rev1, rev2):
        if lpath_exists(target):
            abort('what is the matter, path exists:%s' % target)
        local("mkdir -p '%s'" % target)

        old = SmartName(ver1)
        new = SmartName(ver2)

        MAfiles, Dfiles = self.MAD(self.diff(old, new, rev1, rev2))

        with lcd(target):
            for name in MAfiles:
                if name.dirname not in ('.', '') and not lpath_exists(name.dirname):
                    local("mkdir -p '%s'" % name.dirname)
                with lcd(name.dirname):
                    local('svn export --force %s' % name.spawn(new.tag))
        return Dfiles
