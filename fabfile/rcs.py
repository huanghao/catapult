import os

from fabric.api import abort, local, lcd


def create(rcs_type, *args, **kw):
    if rcs_type.lower().strip() == 'svn':
        return SVN(*args, **kw)
    abort('unknown rcs type:%s' % rcs_type)
    return None # nerver get to this line


class SVN(object):

    def __init__(self, base, version, version_type):
        self.path, self.version = self.make_full_path(base, version, version_type)

    def make_full_path(self, base, version, version_type):
        if version_type == 'ver':
            if version == 'trunk':
                return os.path.join(base, version), version
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

