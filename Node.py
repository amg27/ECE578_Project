from multiprocessing import Process, Pipe
from MessageClass import * 

class Node:

    #The following function are for a switch case look up dictionary thing
    def TxData(self, msg):
        self.txData = msg.data
        self.txdataLen = msg.length
        self.txdataIntOffset = 30
        self.txdataArrayOffset = 0
        return TxDataMessage(self.txData, self.txdataLen)

    def Symbol(self, msg):
        #Rx msg proccessing
        self.getNextRxBits(msg.symbol)

        # send next tx bit
        return SymbolMessage(self.getNextSymbol())


    def Error(self, msg):
        self.error = 1
        return self.error

    def RxData(self, msg):
        return RxDataMessage(data=self.rxData,length=self.rxdataLen)

#todo: include rx status
    def Status(self, msg):
        return StatusMessage([self.txdataLen, self.rxdataLen])

    # init fucntion       
    # mask[] is the index in the symbol array
    # mask[0] is 1 then data is 00
    # mask[1] is 1 then data is 01
    # mask[2] is 1 then data is 11
    # mask[3] is 1 then data is 10
    def __init__(self,seed=1,txmask = [0,1,2,3], rxmask = [16,17,18,19]):
        self.seed = seed
        self.curSymbol = 0
        self.txData = 0
        self.rxData = 0
        self.txdataLen = 0
        self.txdataIntOffset = 30
        self.txdataArrayOffset = 0
        self.rxdataIntOffset = 30
        self.rxdataArrayOffset = 0
        self.rxdataLen = 0
        self.txmask = txmask
        self.rxmask = rxmask
        self.msgFunction = {1 : self.TxData,
                    2 : self.Symbol,
                    4 : self.Error,
                    5 : self.RxData,
                    6 : self.Status,
                    }

    # main running function    
    def runNode(self,conn):
        while conn.poll(2):
            incMsg = conn.recv()
            conn.send(self.msgFunction[incMsg.ty](incMsg))
        conn.close()

    # receive next 2 bits 
    def getNextRxBits(self, symbol):
        s0Mask = 0x80000000 >> self.rxmask[0]
        s1Mask = 0x80000000 >> self.rxmask[1]
        s2Mask = 0x80000000 >> self.rxmask[2]
        s3Mask = 0x80000000 >> self.rxmask[3]
        
        # fix this if longer symbols are used
        if s0Mask & symbol[0] >= 1:
            curBits = 0
        elif s1Mask & symbol[0] >= 1:
            curBits = 1
        elif s2Mask & symbol[0] >= 1:
            curBits = 3
        elif s3Mask & symbol[0] >= 1:
            curBits = 2
        else:
            curBits = 0
        
        self.rxData |= curBits << self.rxdataIntOffset
        self.rxdataIntOffset -= 2
        if self.rxdataIntOffset < 0:
            self.rxdataIntOffset = 30
            self.rxdataArrayOffset += 1
        self.rxdataLen += 2

    # returns the next bit to transmit
    def getNextSymbol(self):
        nextBits = -1
        if self.txdataLen >= 2:
            nextBits = 0x3 & (self.txData[self.txdataArrayOffset] >> self.txdataIntOffset)
            self.txdataIntOffset -= 2
            if self.txdataIntOffset < 0:
                self.txdataIntOffset = 30
                self.txdataArrayOffset += 1
            self.txdataLen -= 2
        elif self.txdataLen == 1:          
            nextBits = (0x2 & self.txData[self.dataArrayOffset]) << self.txdataIntOffset
            self.txdataLen -=1



        if nextBits == 0x0:
            nextSymbol  = 0
        elif nextBits == 0x1:
            nextSymbol  = 1
        elif nextBits == 0x3:
            nextSymbol  = 2
        elif nextBits == 0x2:
            nextSymbol  = 3
        else:
            return 0

        return 0x80000000 >> self.txmask[nextSymbol]   



if __name__ == "__main__":
    txn = Node()
    txn.msgFunction[1](TxDataMessage([0xa50fa50f],31))
    txn.getNextRxBits([0x00000000])
    txn.getNextRxBits([0x00001000])
    txn.getNextRxBits([0x00001000])
    txn.getNextRxBits([0x00004000])
    txn.getNextRxBits([0x00004000])
    txn.getNextRxBits([0x00008000])
    txn.getNextRxBits([0x00008000])
    txn.getNextRxBits([0x00002000])
    txn.getNextRxBits([0x00002000])
    print '%8x'%txn.rxData
