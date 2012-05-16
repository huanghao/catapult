import os


from ops import mine


class Cap(object):

    hier = ['etc',
            'status',
            'releases',
            'run',
            {'log': 'syslog'},
            {'shared': ['log', 'pids', 'system']},
            ]

    def __init__(self, home):
        self.home = home

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
