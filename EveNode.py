from multiprocessing import Process, Pipe
from MessageClass import * 
import zlib
import time
import datetime
import ctypes
from SearchPath import *                


class EveNode:
    def __init__(self):

        self.randA = 3527
        self.randB = 3541
        self.randC = 65536
        seed = 1
        
        self.matchCount = 0
        
        self.searchPaths = []

        self.name = 'eve'
        self.fid = -1
        self.openFile()
        self.luTable = []
        self.GenLUTable()
        self.firstPass = True

    def GenLUTable(self):
        self.luTable = 65536*[None]
        for index in range(65536):
            seed = (self.randA * index + self.randB) % self.randC
            self.luTable[index] = seed >> 10
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

    def CompareOffset(self,curSymbol):
        # get locations of one values
        s = 0x8000000000000000
        offsets = []
        index = 0
        while s > 0:
            if (curSymbol[0] & s) > 0:
                offsets.append(index)
            index += 1
            s = s >> 1
#       print offsets

        
        # check current paths to see if valid
        for path in self.searchPaths:
            if not path.CheckOffsets(offsets):
                self.searchPaths.remove(path)
            # check to see if path won
            if path.progress== 16:
                print 'init seed found: %i'%path.initSeed
                self.searchPaths.remove(path)
        print 'Number of Search Path: %i'%len(self.searchPaths) 
        if len(self.searchPaths) == 1:
            print 'Initseed Guess = %i'%self.searchPaths[0].initSeed
        # create Search Pattern
        # append newpaths
        if self.firstPass:
            newPaths = []
            for off in offsets:
                newPaths.append(self.MatchOne(off))
            if len(newPaths) >= 1:
                self.firstPass = False
                for posSeed in newPaths[0]:
                    if posSeed == 1:
                        print 'yes found'
                    self.searchPaths.append(SearchPath(posSeed))

    # creates a list of possiable init seeds for pattern search
    def MatchOne(self,offset):
        out = []
        for ii in range(65536):
            if self.luTable[ii] == offset:
                out.append(ii)
        return out        

    def openFile(self):
        timeText = datetime.datetime.fromtimestamp(time.time()).strftime('%H%M%S')
        filename = timeText+'_'+self.name
        #print filename
        self.fid = open(filename, 'w')
        self.fid.write('file-opened\n')


if __name__ == '__main__':
    a = EveNode()

    sym = [0b0000001000000000000000000000000000000000000000000000000000000000]
    a.CompareOffset(sym)
    sym = [0b0000000000000000000000000000100000000000000000000000000000000000]
    a.CompareOffset(sym)
    sym = [0b0000000000000000000000000000000000000000000000000000000000000000]
    a.CompareOffset(sym)
    sym = [0b0000000000000000000000000000100000000000000000000000000000000000]
    a.CompareOffset(sym)
    sym = [0b0000000000000000000000000000000000000000010000000000000000000000]
    a.CompareOffset(sym)
    sym = [0b0000000000000000000000000000000000000000000000000000000000000000]
    a.CompareOffset(sym)
    sym = [0b0001000000000000000000000000000000000000000000000000000000000000]
    a.CompareOffset(sym)
    sym = [0b0000000000000000000000000000000000000000000000000000000000000000]
    a.CompareOffset(sym)
    sym = [0b0000000000000000000000000000000000000010000000000000000000000000]
    a.CompareOffset(sym)
    sym = [0b0000000000000000000000000000000000000000000000000000000000000000]
    a.CompareOffset(sym)
    sym = [0b0000000000000000000000000000000000000000000000000000000000000000]
    a.CompareOffset(sym)
    sym = [0b0000000000000000000000000000001000000000000000000000000000000000]
    a.CompareOffset(sym)
    sym = [0b0000000000000000100000000000000000000000000000000000000000000000]
    a.CompareOffset(sym)
    sym = [0b0000000000000000000000000000100000000000000000000000000000000000]
    a.CompareOffset(sym)
    sym = [0b0000000000000000000000000000000000000000010000000000000000000000]
    a.CompareOffset(sym)
    sym = [0b0000000000000000000000000000000000010000000000000000000000000000]
    a.CompareOffset(sym)
    sym = [0b0000000000000000000000000000000000000000000000000000000000000000]
    a.CompareOffset(sym)
    sym = [0b0000000000000000000000000000100000000000000000000000000000000000]
    a.CompareOffset(sym)
    sym = [0b0000000000000000000000000000010000000000000000000000000000000000]
    a.CompareOffset(sym)
    sym = [0b0000000000000000000000000000000000000000000000000000000000000000]
    a.CompareOffset(sym)
    sym = [0b0000000000000000000000000000000000000000010000000000000000000000]
    a.CompareOffset(sym)
    sym = [0b0000000000000000000000100000000000000000000000000000000000000000]
    a.CompareOffset(sym)
    sym = [0b0000000000000000000000000000000000000000000000000000000000000000]
    a.CompareOffset(sym)
    sym = [0b1000000000000000000000000000000000000000000000000000000000000000]
    a.CompareOffset(sym)
    sym = [0b0000000000000000000000000000000000000000000000000000000000000000]
    a.CompareOffset(sym)
    sym = [0b0000000000000000000000000000000000000000000000000100000000000000]
    a.CompareOffset(sym)
    sym = [0b0000000000000000000000000000000000000000000000000000000000000000]
    a.CompareOffset(sym)
    sym = [0b0000000000000000000000000000000000000000000000000000000000000000]
    a.CompareOffset(sym)
    sym = [0b0000000000000000100000000000000000000000000000000000000000000000]
    a.CompareOffset(sym)
    sym = [0b0000000000000000000000000000100000000000000000000000000000000000]
    a.CompareOffset(sym)
    sym = [0b0000000000000000000000000000000000000000010000000000000000000000]
    a.CompareOffset(sym)
    sym = [0b0000000000000000000000000000000000010000000000000000000000000000]
    a.CompareOffset(sym)
    sym = [0b0000000000000000000000000000000000000000000000000000100000000000]
    a.CompareOffset(sym)
    sym = [0b0000000000000000000000000000000000000000000000000000000000000000]
    a.CompareOffset(sym)

    print len(a.searchPaths)
