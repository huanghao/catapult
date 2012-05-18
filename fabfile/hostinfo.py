from fabric.api import env, run, sudo, hide
from fabric.tasks import Task


class hostinfo(Task):

    def run(self, *args, **kw):
        self.query_dmi()

    def query_dmi(self):
        with hide('stdout'):
            dmi = sudo('dmidecode -t system -t processor -t memory').stdout

        info = self.parse(dmi)
        #from pprint import pprint
        #pprint(info)
        #print '-'*10
        def escval(val):
            return None if val in ('Not Specified', '') else val

        sysinfo = escval(info['System Information'][0])
        manufacturer = escval(sysinfo['Manufacturer'])
        product = escval(sysinfo['Product Name'])
        uuid = escval(sysinfo['UUID'])
        serial = escval(sysinfo['Serial Number'])
        cpu = filter(None, [ escval(i['Version']) for i in info['Processor Information'] ])
        sizes = [ i['Size'].split() for i in info['Memory Device'] if i['Size'][0].isdigit() ]
        total = sum([ int(i[0]) for i in sizes ])
        unit = sizes[0][1] # assume that at least one memory and all unit are the same
        memory = '%d %s' % (total, unit)

        print 'manufacturer:', manufacturer
        print 'product:', product
        print 'serial:', serial
        print 'UUID:', uuid
        print 'cpu:', '\n'.join(cpu)
        print 'memory:', memory

    def parse(self, dmi):
        def gen_lines():
            for line in dmi.split('\n'):
                yield line.rstrip()
        lines = gen_lines()

        info = {}
        st = 0

        def section_close():
            try:
                info[section_name].append(section)
            except KeyError:
                info[section_name] = [section]

        while 1:
            try:
                line = lines.next()
            except StopIteration:
                section_close()
                break
                
            if st == 0 and line.startswith('Handle '):
                section_name = lines.next()
                section = {}
                st = 1
            elif st == 1 and line.startswith('\t\t'):
                val = line.lstrip()
                if isinstance(section[key], list):
                    section[key].append(val)
                elif not section[key]:
                    section[key] = val
                else:
                    section[key] = [section[key], val]
            elif st == 1 and line.startswith('\t'):
                key, val = line.lstrip().split(':', 1)
                section[key] = val.strip()
            elif st == 1 and not line:
                section_close()
                st = 0
        return info
