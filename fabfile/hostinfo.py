from fabric.api import env, run, sudo
from fabric.tasks import Task

from state import update_host


def gen_lines(output):
    for line in output.split('\n'):
        yield line.rstrip()


class hostinfo(Task):

    def run(self, *args, **kw):
        uuid, info = self.query_dmi()
        ips = self.query_ip()
        info['name'] = run('hostname').stdout

        update_host(uuid, ips, **info)

    def query_ip(self):
        return self.parse_ip(run('ifconfig').stdout)

    def parse_ip(self, msg):
        for line in gen_lines(msg):
            if not line:
                continue

            flag = line[0].isspace()
            if not flag:
                inter = line.split(':')[0]
                interface = None if inter == 'lo0' else inter
            elif interface:
                cols = line.split()
                if len(cols) > 1:
                    proto, addr = cols[:2]
                    if proto == 'inet':
                        yield interface, proto, addr

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
        lines = gen_lines(dmi)
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
