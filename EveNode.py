from multiprocessing import Process, Pipe
from MessageClass import * 
import zlib
import time
import datetime
import ctypes


class EveNode:
    def __init__(self):

        self.randA = 3527
        self.randB = 3541
        self.randC = 65536
        
        self.name = 'eve'
        self.fid = -1
        self.openFile()
        self.luTable = []
        self.GenLUTable()

    def GenLUTable(self):
        seed = 0
        self.luTable = 65536*[None]
        self.luTable[0] = seed
        for index in range(1,65536):
            seed = (self.randA * seed + self.randB) % self.randC
            self.luTable[index] = seed >> 11
#       proof that the full period is met
#       seed = (self.randA * seed + self.randB) % self.randC
#       print seed>>11
#       seed = (self.randA * seed + self.randB) % self.randC
#       print seed>>11
#       seed = (self.randA * seed + self.randB) % self.randC
#       print seed>>11
#       seed = (self.randA * seed + self.randB) % self.randC
#       print seed>>11
#       seed = (self.randA * seed + self.randB) % self.randC
#       print seed>>11
#       seed = (self.randA * seed + self.randB) % self.randC
#       print seed>>11


    def openFile(self):
        timeText = datetime.datetime.fromtimestamp(time.time()).strftime('%H%M%S')
        filename = timeText+'_'+self.name
        #print filename
        self.fid = open(filename, 'w')
        self.fid.write('file-opened\n')


if __name__ == '__main__':
    a = EveNode()
    print '----------'
    for ii in range(10):
        print a.luTable[ii]

