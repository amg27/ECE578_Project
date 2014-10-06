from multiprocessing import Process, Pipe
from MessageClass import TxDataMessage, SymbolMessage, StatusMessage

class TxNode:

    #The following function are for a switch case look up dictionary thing
    def TxData(self, msg):
        self.txData = msg.data
        self.dataLen = msg.length
        self.dataIntOffset = 0
        self.dataArrayOffset = 0
        return self.txData

    def Symbol(self, msg):
        self.curSymbol = msg.symbol
        #todo: rx msg proccessing
       
        # send next tx bit
        return SymbolMessage(self.getNextSymbol())


    def Error(self, msg):
        self.error = 1
        return self.error

    def RxData(self, msg):
        return 0

#todo: include rx status
    def Status(self, msg):
        return StatusMessage(self.dataLen)

    # init fucntion       
    # mask[] is the index in the symbol array
    # mask[0] is 1 then data is 00
    # mask[1] is 1 then data is 01
    # mask[2] is 1 then data is 11
    # mask[3] is 1 then data is 10
    def __init__(self,seed=1,mask = [0,1,2,3]):
        self.seed = seed
        self.curSymbol = 0
        self.txData = 0
        self.dataLen = 0
        self.dataIntOffset = 0
        self.dataArrayOffset = 0
        self.mask = mask
        self.msgFunction = {1 : self.TxData,
                    2 : self.Symbol,
                    4 : self.Error,
                    5 : self.RxData,
                    6 : self.Status,
                    }

    # main running function    
    def runTxNode(self,conn):
        while conn.poll(2):
            incMsg = conn.recv()
            conn.send(self.msgFunction[incMsg.ty](incMsg))
        conn.close()

    # returns the next bit to transmit
    def getNextSymbol(self):
        nextBits = -1
        if self.dataLen >= 2:
            nextBits = (0x3 & self.txData[self.dataArrayOffset]) << self.dataIntOffset
            self.dataIntOffset += 2
            if self.dataIntOffset == 32:
                self.dataIntOffset = 0
                self.dataArrayOffset += 1
            self.dataLen -= 2
        elif self.dataLen == 1:          
            nextBits = (0x2 & self.txData[self.dataArrayOffset]) << self.dataIntOffset
            self.dataLen -=1



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

        return 0x80000000 >> self.mask[nextSymbol]   
