from subprocess import Popen, PIPE, STDOUT


proc = None

def run(cmd):
    #TODO: how to cancel the background fab job
    global proc
    proc = p = Popen(cmd, stdout=PIPE, stderr=STDOUT, bufsize=1)
    while 1:
        line = p.stdout.readline()
        if not line:
            break
        #FIXME: still have problem with the output
        # now the output is not yield by linewise
        # maybe the fab process buffered its output
        yield line

def stop():
    global proc
    p = proc
    proc = None
    
    if p and p.poll() is None:
        p.terminate()
        p.wait()
        return 'killed'
    return 'null'

def fab():
    import os
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        '..', '..', 'fabfile')
    return run([
            '/usr/local/bin/fab',
            '-f',
            path,
            '-H',
            '172.16.26.38,172.16.26.39',
            'setup:nds'])



if __name__ == '__main__':
    def sig_handler(sig, stack):
        print 'recv %d' % sig

    import signal
    signal.signal(signal.SIGINT, sig_handler)

    for line in fab():
        print line,
