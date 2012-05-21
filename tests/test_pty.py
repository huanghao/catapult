import os
import pty
import select
import signal
import time

master, slave = pty.openpty()

pid = os.fork()
if pid == 0:
    os.close(master)
    os.dup2(slave, 0)
    os.dup2(slave, 1)
    os.dup2(slave, 2)
    if slave > 2:
        os.close(slave)
    os.execlp('python', 'python', './echo.py')
else:
    os.close(slave)
    os.write(master, "abc")
    while 1:
        msg = os.read(master, 1024)
        if not msg:
            break
        print '<<', msg, '>>'
        time.sleep(1)
        os.kill(pid, signal.SIGINT)
    os.waitpid(pid, 0)
    print 'end'
