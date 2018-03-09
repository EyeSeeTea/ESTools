import os


def daemonize():
    "Convert calling process into a daemon"
    detach()       # unblock grandparent, ensure we are not process group leader
    os.setsid()    # become the session and new process group leader (now, yes),
                   # so we don't die with the parent
    detach()       # so we are not session leader and can safely open a terminal
    os.chdir('/')  # working dir, so we can unmount the original filesystem
    os.umask(0)    # file mode creation mask, so we don't just inherit it

    close_fds()    # close all file descriptors, don't use original terminal
    open_stdds()   # open standard descriptors, so subprocesses can use them


def detach():
    pid = os.fork()
    if pid > 0:
        os._exit(0)  # allow the parent process to terminate


def close_fds():
    for fd in range(1024):
        try:
            os.close(fd)
        except OSError:
            pass  # fd wasn't open to begin with (ignore)


def open_stdds():
    os.open(os.devnull, os.O_RDWR)  # standard input (0)
    os.dup2(0, 1)  # standard output
    os.dup2(0, 2)  # standard error
