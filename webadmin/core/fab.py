import os
import pty
import signal


pid = None #FIXME: only for demo

def run(*args):
    master, slave = pty.openpty()
    global pid
    pid = os.fork()
    if pid == 0:
        os.close(master)
        #os.dup2(slave, 0)
        os.dup2(slave, 1)
        os.dup2(slave, 2)
        if slave > 2:
            os.close(slave)
        os.execlp(args[0], *args)
    else:
        os.close(slave)
        while 1:
            msg = os.read(master, 1024)
            if not msg:
                break
            yield msg
        os.close(master)
        os.waitpid(pid, 0)
        pid = None


def term():
    os.kill(pid, signal.SIGINT)
    return 'killed %d' % pid


def run_test():
    dirname = os.path.dirname(os.path.abspath(__file__))
    return run('python',
               os.path.join(dirname,
                            '..',
                            '..',
                            'tests',
                            'test.py'))


if __name__ == '__main__':
    for output in run_test():
        os.write(1, output)
