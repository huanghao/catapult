import os
import datetime

from fabric.api import runs_once, local, lcd, cd, abort
from fabric.contrib import project

from state import myenv
from ops import mc, relink_current_rel, get_current_rel, mark, svn_revision, path_exists


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
            self.repo = myenv.svn
            self.tag, self.base = (fpor.split('/', 1)+[''])[:2]

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


def get_local_time():
    return datetime.datetime.now().strftime('%Y%m%d%H%M%S')


def fetch_changelist(old, new, rev1, rev2):
    cmd = ['svn diff --summarize',
           '--old=' + str(old),
           '--new=' + str(new),
           ]

    if rev1 and rev2:
        cmd.append('-r%s:%s' % (rev1, rev2))
    return local(' '.join(cmd), capture=True).stdout


def parse_changelist(svnlog):
    print 'CHANGE HISTORY:'
    print svnlog
    print '-'*10
    for line in svnlog.split('\n'):
        action, path = line.split()
        yield action, SmartName(path)


@runs_once
def prepare_inc(old, new, rev1, rev2):
    if old == new and rev1 == rev2:
        abort('can not deploy a duplicated (version, revision):(%s, %s)' % (new.tag, rev1))

    svnlog = fetch_changelist(old, new, rev1, rev2).strip()
    if not svnlog:
        abort('no difference was found between two versions:%s:%s:%s:%s' % (old.tag, new.tag, rev1, rev2))

    dfiles = []
    rfiles = []
    for action, path in parse_changelist(svnlog):
        if action == 'D':
            dfiles.append(path)
        else:
            rfiles.append(path)

    return make_inc_workcopy(rfiles, new), dfiles

def make_inc_workcopy(rfiles, new):
    hid = get_local_time()
    hdir = os.path.join(myenv.ltmp, hid)
    local('mkdir %s' % hdir)

    with lcd(hdir):
        for fname in rfiles:
            dname = os.path.dirname(fname.base)
            if dname:
                if not path_exists(dname):
                    local('mkdir -p %s' % dname)
                with lcd(dname):
                    local('svn export --force %s' % fname.spawn(new.tag))
            else:
                local('svn export --force %s' % fname.spawn(new.tag))

    rev = svn_revision(str(new))
    mark(hdir, str(new), rev)

    return hid, hdir

def apply_timeline(tag, ver, rev1=None, rev2=None):
    old = SmartName(tag)
    new = SmartName(ver)

    (hotfix_id, lhotfix), dfiles = prepare_inc(old, new, rev1, rev2)

    hotfix = backup(hotfix_id)
    overwrite(lhotfix, hotfix)
    remove_useless(hotfix, dfiles)
    relink_current_rel(hotfix)


def backup(hotfix_id):
    curr = get_current_rel()
    hotfix = '%s_%s' % (curr, hotfix_id)
    mc('cp -r %s %s' % (curr, hotfix)) #FIXME: this cp will break up the normal rollback chain
    return hotfix


def overwrite(lhotfix, hotfix):
    with cd(myenv.tmp):
        project.upload_project(lhotfix, myenv.tmp)
        mc('cp -r %s/* %s' % (os.path.basename(lhotfix), hotfix))


def remove_useless(hotfix, dfiles):
    with cd(hotfix):
        for fname in dfiles:
            mc('rm -rf %s' % fname.base)
