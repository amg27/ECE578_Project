
class SearchPath:
    def __init__(self,seed):
        self.initSeed = seed
        self.randA = 3527
        self.randB = 3541
        self.randC = 65536
        self.nextSeed = (self.randA * seed + self.randB) % self.randC
        self.progress = 1 # current offset to look at
        self.searchPattern = [1,1,0,1,1,0,1,0,1,0,0,1,1,1,1,1]

    def CheckOffsets(self,offsets):
        # get next offset
        self.nextSeed = (self.randA * self.nextSeed + self.randB) % self.randC
        val = self.nextSeed >> 10
#       if self.initSeed == 1:
#           print 'next look for val is: %i'%val

        passed = False
        for off in offsets:
            if val == off and self.searchPattern[self.progress] == 1:
                passed = True
            if val != off and self.searchPattern[self.progress] == 0:
                passed = True
        if len(offsets) == 0 and self.searchPattern[self.progress] == 0:        
                passed = True
        self.progress += 1
        return passed
                
if __name__ == '__main__':
    a = SearchPath(1)
    print 'passed :%i'%a.CheckOffsets([28])
    print 'passed :%i'%a.CheckOffsets([])
    print 'passed :%i'%a.CheckOffsets([28])
    print 'passed :%i'%a.CheckOffsets([41])
    print 'passed :%i'%a.CheckOffsets([])
    print 'passed :%i'%a.CheckOffsets([3])
    print 'passed :%i'%a.CheckOffsets([])
    print 'passed :%i'%a.CheckOffsets([38])
    print 'passed :%i'%a.CheckOffsets([])
    print 'passed :%i'%a.CheckOffsets([])
    print 'passed :%i'%a.CheckOffsets([30])
    print 'passed :%i'%a.CheckOffsets([16])
    print 'passed :%i'%a.CheckOffsets([28])
    print 'passed :%i'%a.CheckOffsets([41])
    print 'passed :%i'%a.CheckOffsets([35])
    print 'over all passed :%i'%a.progress
