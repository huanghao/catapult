#include <stdio.h>
//#include <pty.h>
//#include <utmp.h>
#include <sys/types.h>
#include <sys/ioctl.h>
#include <termios.h>
#include <libutil.h>

int main(void)
{
    int fdm, fds, n;
    char name[1024];

    openpty(&fdm, &fds, name, 0, 0);
    printf("tty: %s\n", name);

    if (fork() == 0) {
        close(fdm);
        close(1);
        dup(fds);
        close(2);
        dup(fds);
        execlp("python", "python", "/home/huanghao/workspace/catapult/tests/echo.py", 0);
    } else {
        close(fds);
        while ((n = read(fdm, name, sizeof(name))) > 0)
        {
            printf("\n>>%.*s", n, name);
        }
    }
    return 0;
}
