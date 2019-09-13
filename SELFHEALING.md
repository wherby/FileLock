# Pessimist’s file lock

For software design when needs a global lock cross process, the file lock will be the simplest choose. While both Posix based system(Linux, Ubuntu, Macos, etc.) and Windows system have different file lock function, then the universal lock can be write as below:

```python

try:
    # Posix based file locking (Linux, Ubuntu, MacOS, etc.)
    import fcntl, os
    def lock_file(f):
        fcntl.lockf(f, fcntl.LOCK_EX)
    def unlock_file(f):
        fcntl.lockf(f, fcntl.LOCK_UN)
except ModuleNotFoundError:
    # Windows file locking
    import msvcrt, os
    def file_size(f):
        return os.path.getsize( os.path.realpath(f.name) )
    def lock_file(f):
        msvcrt.locking(f.fileno(), msvcrt.LK_RLCK, file_size(f))
    def unlock_file(f):
        msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, file_size(f))
```

And there is another implementation which cross all platform https://github.com/dmfrey/FileLock, user could easily use the FileLock as below:

``` Python 

from filelock import FileLock

with FileLock("myfile.txt"):
    # work with the file as it is now locked
    print("Lock acquired.")

```

The FileLock use a universal way to create a global lock which is to detect weather specified file is on disk or not as below:

``` Python 

    def acquire(self):
        """ Acquire the lock, if possible. If the lock is in use, it check again
            every `wait` seconds. It does this until it either gets the lock or
            exceeds `timeout` number of seconds, in which case it throws 
            an exception.
        """
        start_time = time.time()
        while True:
            try:
                self.fd = os.open(self.lockfile, os.O_CREAT|os.O_EXCL|os.O_RDWR)
                self.is_locked = True #moved to ensure tag only when locked
                break;
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise
                if self.timeout is None:
                    raise FileLockException("Could not acquire lock on {}".format(self.file_name))
                if (time.time() - start_time) >= self.timeout:
                    raise FileLockException("Timeout occured.")
                time.sleep(self.delay)
#        self.is_locked = True
 
 
    def release(self):
        """ Get rid of the lock by deleting the lockfile. 
            When working in a `with` statement, this gets automatically 
            called at the end.
        """
        if self.is_locked:
            os.close(self.fd)
            os.unlink(self.lockfile)
            self.is_locked = False

```

If the lockfile is not created then the lock could be acquired and the lockfile is created, and when release the lock, the file is removed from disk.

It’s easy understanding and feasible on Posix and Windows, but what’s if when the lock is acquired and system reboot, then the file is already on disk, the lock will be a dead lock.

How could we create a self-healed FileLock?
Under some restriction, the self-healed FileLock could be created, when user could define a max lock time(lockvanishtime) for same FileLock.

``` Python

    def readLastTime(self):
        try:
            with open(self.logtimefile,"r+") as f:
                time = f.read()
                return float(time)
        except Exception as inst:
            print("read time failed")
            print(inst)
            pass

    def recordLockTime(self):
        try:
            with open(self.logtimefile, "w") as f:
                f.writelines(str(time.time()))
        except Exception as inst:
            print("record lock failed")
            print(inst)
            pass
 
    def acquire(self):
        """ Acquire the lock, if possible. If the lock is in use, it check again
            every `wait` seconds. It does this until it either gets the lock or
            exceeds `timeout` number of seconds, in which case it throws 
            an exception.
        """
        start_time = time.time()
        while True:
            try:
                self.fd = os.open(self.lockfile, os.O_CREAT|os.O_EXCL|os.O_RDWR)
                self.is_locked = True #moved to ensure tag only when locked
                self.recordLockTime()
                break;
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise
                if self.timeout is None:
                    raise FileLockException("Could not acquire lock on {}".format(self.file_name))
                if (time.time() - start_time) >= self.timeout:
                    lastTime =self.readLastTime()
                    if (time.time() - lastTime) > self.lockvanishtime:
                        os.remove(self.lockfile)
                    raise FileLockException("Timeout occured.")
                time.sleep(self.delay)

```

When lock is acquired, the lock start time will be recorded in logtimefile, when lock timeout, there will be a check if that lock is locked more that the lockvanishtime. When lock time is more than the lockvanishtime, the file will be removed, then dead lock is resolved.
