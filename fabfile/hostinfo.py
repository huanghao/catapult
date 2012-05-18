import re

from fabric.api import run, sudo, task

from state import update_host


ipv4 = re.compile(r'\d+\.\d+\.\d+\.\d+')


def gen_lines(output):
    for line in output.split('\n'):
        yield line.rstrip()


@task
def hostinfo():
    '''
    query host info such as uuid,cpu,memory.. and save to db
    '''
    uuid, info = query_dmi()
    ips = query_ip()
    info['name'] = run('hostname').stdout
    update_host(uuid, ips, **info)


def query_ip():
    return parse_ip(run('ifconfig').stdout)

def parse_ip(msg):
    for line in gen_lines(msg):
        if not line:
            continue

        flag = line[0].isspace()
        if not flag:
            inter = line.split(None, 1)[0].rstrip(':')
            interface = None if inter.startswith('lo') else inter
        elif interface:
            cols = line.split()
            if len(cols) > 1:
                proto, addr_string = cols[:2]
                if proto == 'inet':
                    addr = re.findall(ipv4, addr_string)[0]
                    yield interface, proto, addr

def query_dmi():
    dmi = sudo('dmidecode -t system -t processor -t memory').stdout

    info = parse_dmi(dmi)
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

def parse_dmi(dmi):
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
