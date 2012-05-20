import os
import pty


def run(*args):
    pid, fd = pty.fork()
    if pid == 0:
        os.execlp(*args)
        #child never gets here

    while 1:
        try:
            output = os.read(fd, 1024)
        except OSError, e:
            #TODO: find a nice way to do it
            if e.errno == 5: #slave fd had close by chlid
                output = ''
            else:
                raise

        if not output:
            break
        yield output
    os.waitpid(pid, 0)


def run_test():
    dirname = os.path.dirname(os.path.abspath(__file__))
    return run('python', 'python',
               os.path.join(dirname, '..', '..', 'tests', 'test.py'))


if __name__ == '__main__':
    for output in run_test():
        print output,
