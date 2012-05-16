import os

from fabric.api import abort, cd, runs_once, prompt, run, env
from fabric.contrib import project

from state import myenv
from ops import ProjTask
import rcs
import schemas


class deploy(ProjTask):

    def work(self, ver=None, *args, **kw):
        self.pre()

        if ver is None:
            ver = prompt('No version found. Please specify version:')

        self.deploy(ver, *args, **kw)

        self.post()

    def pre(self):
        if 'pre_deploy' in myenv:
            for cmd in myenv.pre_deploy:
                run(cmd)
    
    def post(self):
        if 'post_deploy' in myenv:
            for cmd in myenv.post_deploy:
                run(cmd)

    def deploy(self, ver, ver_type='ver', *args, **kw):
        rc = rcs.create(myenv.cvs_model, myenv.cvs_path, ver, ver_type)
        schema = schemas.Cap(myenv.home)

        pid, workcopy = self.make_workcopy(rc, schema)

        self.upload(schema, workcopy, pid)

        schema.save_current_for_rollback(pid) #TODO: move these two lines to self.work, it's same in ideploy task
        schema.switch_current_to(pid)

    @runs_once #runs_once is incompatible with --parallel
    def make_workcopy(self, rc, schema):
        pid = get_local_time()
        workcopy = os.path.join(myenv.ltmp, pid)

        rc.export(workcopy)
        schema.mark(rc, workcopy)
        return pid, workcopy

    def upload(self, schema, workcopy, pid):
        with cd(myenv.tmp):
            #FIXME: i think it a bug
            #when calling the upload_project function,
            #must cd to remote target directory,
            #otherwise it will fail to find the uploaded file.

            #TODO: this function will do tar,untar,remove many times in localhost
            project.upload_project(workcopy, myenv.tmp)
        schema.copy_to_release(os.path.join(myenv.tmp, pid), pid)
        #FIXME: this is a bug, if localhost is one of the remote hosts,
        #workcopy dir and upload target dir are the same
        #and this rm will remove the dir,
        #when comming the second host, deploy will failed to find the workcopy dir
        #sudo('rm -rf %s' % os.path.join(myenv.tmp, pid))


class check(ProjTask):

    def work(self, *args, **kw):
        schema = schemas.Cap(myenv.home)

        info = schema.tag_info()
        self.check_same(info)

    def check_same(self, info):
        if not hasattr(self, '_info'):
            self._info = info
        elif self._info != info:
            abort('corrupt version %s on host %s' % (str(info), env.host))


class ideploy(deploy):

    def deploy(self, ver, rev1=None, rev2=None, *args, **kw):
        schema = schemas.Cap(myenv.home)
        tag1 = schema.tag_info()['TAG']

        with cd(myenv.home):
            old = SmartName(tag1)
            new = SmartName(ver)

            (hotfix_id, lhotfix), dfiles = prepare_inc(old, new, rev1, rev2)

            hotfix = backup(hotfix_id)
            overwrite(lhotfix, hotfix)
            remove_useless(hotfix, dfiles)
            relink_current_rel(hotfix)






import os
import datetime

from fabric.api import runs_once, local, lcd, cd, abort
from fabric.contrib import project

from state import myenv
from ops import mine, relink_current_rel, get_current_rel, mark, lpath_exists


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
                if not lpath_exists(dname):
                    local('mkdir -p %s' % dname)
                with lcd(dname):
                    local('svn export --force %s' % fname.spawn(new.tag))
            else:
                local('svn export --force %s' % fname.spawn(new.tag))

    print new
    rev = svn_revision(str(new))
    mark(hdir, str(new), rev)

    return hid, hdir


def backup(hotfix_id):
    curr = get_current_rel()
    hotfix = '%s_%s' % (curr, hotfix_id)
    mine('cp -r %s %s' % (curr, hotfix)) #FIXME: this cp will break up the normal rollback chain
    return hotfix


def overwrite(lhotfix, hotfix):
    with cd(myenv.tmp):
        project.upload_project(lhotfix, myenv.tmp)
        mine('cp -r %s/* %s' % (os.path.basename(lhotfix), hotfix))


def remove_useless(hotfix, dfiles):
    with cd(hotfix):
        for fname in dfiles:
            mine('rm -rf %s' % fname.base)
