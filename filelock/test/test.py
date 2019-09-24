import sys
sys.path.append("..")
from filelock import FileLock  
import time

with FileLock(file_name= "myfile.txt"):
    time.sleep(5)
    # work with the file as it is now locked
    print("Lock acquired.")