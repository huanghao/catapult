from fabric.api import abort, local, lcd


class Git(object):

    def __init__(self, base, version):
        self.path = base
        self.version = version

    def export(self, target):
        local("git clone '%s' '%s'" % (self.path, target))
        with lcd(target):
            if self.version is not None:
                local("git checkout '%s'" % self.version)
            local("rm -rf .git")

    @property
    def ver(self):
        return 'HEAD' if self.version is None else self.version
    rev = ver

    def __str__(self):
        return self.path

    def iexport(self, *args, **kw):
        abort('git does not support ideploy')
