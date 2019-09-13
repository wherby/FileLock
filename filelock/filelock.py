#https://github.com/dmfrey/FileLock/blob/master/filelock/filelock.py
import os
import time
import errno
 
class FileLockException(Exception):
    pass
 
class FileLock(object):
    """ A file locking mechanism that has context-manager support so 
        you can use it in a with statement. This should be relatively cross
        compatible as it doesn't rely on msvcrt or fcntl for the locking.
    """
 
    def __init__(self, file_name, timeout=10, delay=.05, logtimefile = "logtime", lockvanishtime = 60, lockfolder=None):
        """ Prepare the file locker. Specify the file to lock and optionally
            the maximum timeout and the delay between each attempt to lock.
        """
        if timeout is not None and delay is None:
            raise ValueError("If timeout is not None, then delay must not be None.")
        self.is_locked = False
        self.lockfolder = os.getcwd()
        if lockfolder != None:
            self.lockfolder = lockfolder
        self.lockfile = os.path.join(self.lockfolder, "%s.lock" % file_name)
        print(self.lockfile)
        print(lockfolder)
        self.file_name = file_name
        self.timeout = timeout
        self.delay = delay
        self.logtimefile =os.path.join(self.lockfolder, "%s.lock" % logtimefile)  
        self.lockvanishtime = lockvanishtime
    
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
 
 
    def __enter__(self):
        """ Activated when used in the with statement. 
            Should automatically acquire a lock to be used in the with block.
        """
        if not self.is_locked:
            self.acquire()
        return self
 
 
    def __exit__(self, type, value, traceback):
        """ Activated at the end of the with statement.
            It automatically releases the lock if it isn't locked.
        """
        if self.is_locked:
            self.release()
 
 
    def __del__(self):
        """ Make sure that the FileLock instance doesn't leave a lockfile
            lying around.
        """
        self.release()