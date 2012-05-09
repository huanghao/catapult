from fabric.api import runs_once

from state import myenv


class SmartName(object):

    def __init__(self, name):
        if self.is_svn_path(name):
            self.full = name
            self.short = self.to_short(name)
        else:
            self.short = name
            self.full = os.path.join(myenv.svn, name)

    def to_short(self, name):
        short = name.replace(myenv.svn, '')
        if self.is_svn_path(short):
            abort('inapprehensive name:%s' % name)
        if short.startswith('/'):
            return short[1:]
        return short

    def is_svn_path(self, name):
        return '://' in name

    def __str__(self):
        return self.short


class TagName(SmartName):

    def __init__(self, name):
        if self.is_svn_path(name):
            super(TagName, self).__init__(name)
        else:
            super(TagName, self).__init__(os.path.join('tags', name))
        tags, self.tag = self.short.split('/')
        if tags != 'tags':
            abort('illegal tag url:%s' % name)


def get_local_time():
    return datetime.datetime.now().strftime('%Y%m%d%H%M%S')


def fetch_changelist(old, new, rev1=None, rev2=None):
    cmd = ['svn diff --summarize ',
           '--old=', old,
           '--new=', new,
           ]

    if rev1 and rev2:
        cmd += [' -r',
                str(rev1),
                ':',
                str(rev2),
                ]
    return local(cmd, capture=True).stdout


def parse_changelist(svnlog):
    for line in svnlog.split('\n'):
        action, path = line.split()
        yield action, path


@runs_once
def build_timeline():
    svn = 'https://svn.intra.umessage.com.cn/repos/paymix/docnotify'
    
    old = os.path.join(svn, 'tags', tag1)
    new = os.path.join(svn ,'tags', tag2)
    svnlog = fetch_changelist(old, new)

    dfiles = []
    rfiles = []
    for action, path in parse_changelist(svnlog):
        if action == 'D':
            dfiles.append(path)
        else:
            rfiles.append(path)

    rdir = make_local_replace_files_copy(rfiles)

    return rdir, dfiles

def make_local_replace_files_copy(rfiles):
    hotfix = os.path.join(myevn.ltmp, get_local_time())
    local('mkdir %s' % hotfix)

    with lcd(hotfix):
        for fname in rfiles:
            dname = os.path.dirname(fname)
            local('mkdir -p %s' % dname)
            with lcd(dname):
                local('svn export %s' % fname)
                
    return hotfix

def apply_timeline():
    rdir, dfiles, hotfix_id = build_timeline()

    hotfix = backup(hotfix_id)
    overwrite(rdir)
    remove_useless(dfiles)
    relink_cur_rel(hotfix)

def backup(hotfix_id):
    curr = get_current_rel()
    hotfix = '%s.hotfix.%s' % (curr, hotfix_id)
    mc('cp -r %s %s' % (curr, hotfix)) #FIXME: this cp will break up the normal rollback chain
    return hotfix

def overwrite(hotfix, rdir):
    project.upload_project(rdir, myenv.tmp)
    with cd(myenv.tmp):
        mc('cp -r %s %s' % rdir, hotfix)

def remove_useless(hotfix, dfiles):
    with cd(myenv.home):
        for fname in dfiles:
            mc('rm -f %s' % fname)
