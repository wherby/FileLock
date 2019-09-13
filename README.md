
========
FileLock
========

    A file locking mechanism that has context-manager support so 
    you can use it in a with statement. This should be relatively cross
    compatible as it doesn't rely on msvcrt or fcntl for the locking.
    

    Originally posted at http://www.evanfosmark.com/2009/01/cross-platform-file-locking-support-in-python/

====
Self healing feature 
====

[Pessimist’s file lock](./SELFHEALING.md)