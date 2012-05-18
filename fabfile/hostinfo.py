from fabric.api import env, run, sudo
from fabric.tasks import Task

from state import update_host


class hostinfo(Task):

    def run(self, *args, **kw):
        uuid, info = self.query_dmi()
        ips = self.query_ip()
        info['name'] = run('hostname').stdout

        update_host(uuid, ips, **info)

    def query_ip(self):
        msg = run('ifconfig').stdout
        ips = filter(lambda (proto, addr): proto == 'inet' and addr not in ('127.0.0.1', '::1'),
                     [ line.split()[:2] for line in msg.split('\n') \
                           if 'inet' in line ])
        return ips

    def query_dmi(self):
        dmi = sudo('dmidecode -t system -t processor -t memory').stdout

        info = self.parse_dmi(dmi)
        sysinfo = info['System Information'][0]

        manufacturer = sysinfo['Manufacturer']
        product = sysinfo['Product Name']
        uuid = sysinfo['UUID']
        serial = sysinfo['Serial Number']

        cpu = [ i['Version'] for i in info['Processor Information']]

        sizes = [ i['Size'].split() for i in info['Memory Device'] if i['Size'][0].isdigit() ]
        total = sum([ int(i[0]) for i in sizes ])
        unit = sizes[0][1] # assume that at least one memory and all unit are the same
        memory = '%d %s' % (total, unit)

        return uuid, {'manufacturer': manufacturer,
                      'product': product,
                      'serial': serial,
                      'cpu': '\n'.join(cpu),
                      'memory': memory,
                      }

    def parse_dmi(self, dmi):
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
