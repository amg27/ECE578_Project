from multiprocessing import Process, Pipe
from MessageClass import * 

class Node:

    #The following function are for a switch case look up dictionary thing
    def TxData(self, msg):
        self.timeStamp = msg.timeStamp
        txDataLoc = [self.header] + msg.data
        
        # encode with convolutional encoder
        d1 = False
        d2 = False
        bitLoc = 0x80000000
        intOff = 0
        outBitLoc = 31
        outIntOff = 0
        for ii in range(0,msg.length + 32):
            cb = txDataLoc[intOff] & bitLoc > 0
            b0 = d1 ^ d2 ^ cb
            b1 = d2 ^ cb

            d2 = d1
            d1 = cb

            bitLoc = bitLoc >> 1;
            if bitLoc == 0:
                bitLoc = 0x80000000
                intOff += 1
            
            self.txData[outIntOff] |= (1 if b0 else 0) << outBitLoc
            outBitLoc -= 1
            self.txData[outIntOff] |= (1 if b1 else 0) << outBitLoc
            outBitLoc -= 1
            if outBitLoc == -1:
                outBitLoc = 31
                outIntOff += 1
                self.txData.append(0)
        # setup transmit params
        self.txdataLen = (outIntOff + 1) * 32 # for the header 
        self.txdataIntOffset = 31
        self.txdataArrayOffset = 0
        return TxDataMessage(self.txData, self.txdataLen)

    def Symbol(self, msg):
        self.timeStamp = msg.timeStamp
        #Rx msg proccessing
        self.getNextRxBits(msg.symbol)

        # send next tx bit
        return SymbolMessage(self.getNextSymbol())


    def Error(self, msg):
        self.timeStamp = msg.timeStamp
        self.error = 1
        return self.error

    def RxData(self, msg):
        self.timeStamp = msg.timeStamp
        return RxDataMessage(data=self.rxData,length=self.rxdataLen, ts=self.timeStamp)

#todo: include rx status
    def Status(self, msg):
        self.timeStamp = msg.timeStamp
        return StatusMessage([self.txdataLen, self.rxdataLen])

    # init fucntion       
    # mask[] is the index in the symbol array
    # mask[0] is 1 then data is 0
    # mask[1] is 1 then data is 1
    # header in 13bit barker code then link id then 11 bit barker code
    def __init__(self,seed=1,txmask = [0,1], rxmask = [16,17], header=0xf9a80712):
        self.seed = seed
        self.curSymbol = 0
        self.header = header
        
        # Tx Variables
        self.txData = [0]
        self.txdataLen = 0
        self.txdataIntOffset = 31
        self.txdataArrayOffset = 0

        # Receive Variables
        self.rxData = [0]
        self.rxdataIntOffset = 31
        self.rxdataArrayOffset = 0
        self.rxdataLen = 0
        self.rxHeaderFound = False
        self.rxBuffer = 0
        self.rxBufferBit = True
        self.rxPrevState = 0
        self.rxHeaderMask = 0x80000000
        self.rxErrorDetect = False


        self.txmask = txmask
        self.rxmask = rxmask
        seld.timeStamp = 0
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
        
        # fix this if longer symbols are used
        if s0Mask & symbol[0] >= 1:
            curBit = 0
        elif s1Mask & symbol[0] >= 1:
            curBit = 1
        else:
            curBit = 0

        if self.rxBufferBit: # Store current bit
            self.rxBuffer |= curBit
            self.rxBufferBit = False
        else: # get current state
            self.rxBuffer = self.rxBuffer << 1;
            self.rxBuffer |= curBit
            self.rxBufferBit = True
            rxCurState = self.rxBuffer
            self.rxBuffer = 0;
            
            # Get Data
            rxBit = -1
            prevRxBit = -1
            if self.rxPrevState == 0:
                if self.rxErrorDetect:
                    if rxCurState == 0:
                        rxBit = 0
                        prevRxBit = 0
                        self.rxPrevState = 0
                    elif rxCurState == 1:
                        rxBit = 1
                        prevRxBit = 1
                        self.rxPrevState = 3
                    elif rxCurState == 2:
                        rxBit = 0
                        prevRxBit = 1
                        self.rxPrevState = 1
                    elif rxCurState == 3:
                        rxBit = 1
                        prevRxBit = 0
                        self.rxPrevState = 2
                elif rxCurState == 0:
                    rxBit = 0
                    self.rxPrevState = 0
                elif rxCurState == 3:
                    rxBit = 1
                    self.rxPrevState = 2
                else:
                    self.rxErrorDetect = True
                    return
            elif self.rxPrevState == 2:
                if self.rxErrorDetect:
                    if rxCurState == 0:
                        rxBit = 1
                        prevRxBit = 0
                        self.rxPrevState = 2
                    elif rxCurState == 1:
                        rxBit = 0
                        prevRxBit = 1
                        self.rxPrevState = 1
                    elif rxCurState == 2:
                        rxBit = 1
                        prevRxBit = 1
                        self.rxPrevState = 3
                    elif rxCurState == 3:
                        rxBit = 0
                        prevRxBit = 0
                        self.rxPrevState = 0
                elif rxCurState == 2:
                    rxBit = 0
                    self.rxPrevState = 1
                elif rxCurState == 1:
                    rxBit = 1
                    self.rxPrevState = 3
                else:
                    self.rxErrorDetect = True
                    return
            elif self.rxPrevState == 1:
                if self.rxErrorDetect:
                    if rxCurState == 0:
                        rxBit = 0
                        prevRxBit = 0
                        self.rxPrevState = 0
                    elif rxCurState == 1:
                        rxBit = 1
                        prevRxBit = 1
                        self.rxPrevState = 3
                    elif rxCurState == 2:
                        rxBit = 0
                        prevRxBit = 1
                        self.rxPrevState = 1
                    elif rxCurState == 3:
                        rxBit = 1
                        prevRxBit = 0
                        self.rxPrevState = 2
                elif rxCurState == 3:
                    rxBit = 0
                    self.rxPrevState = 0
                elif rxCurState == 0:
                    rxBit = 1
                    self.rxPrevState = 2
                else:
                    self.rxErrorDetect = True
                    return
            elif self.rxPrevState == 3:
                if self.rxErrorDetect:
                    if rxCurState == 0:
                        rxBit = 1
                        prevRxBit = 0
                        self.rxPrevState = 2
                    elif rxCurState == 1:
                        rxBit = 0
                        prevRxBit = 1
                        self.rxPrevState = 1
                    elif rxCurState == 2:
                        rxBit = 1
                        prevRxBit = 1
                        self.rxPrevState = 3
                    elif rxCurState == 3:
                        rxBit = 0
                        prevRxBit = 0
                        self.rxPrevState = 0
                elif rxCurState == 1:
                    rxBit = 0
                    self.rxPrevState = 1
                elif rxCurState == 2:
                    rxBit = 1
                    self.rxPrevState = 3
                else:
                    self.rxErrorDetect = True
                    return
            else:
                self.rxErrorDetect = True
                return

            # add to data payload
            if self.rxHeaderFound:
                if self.rxErrorDetect:
                    self.rxData[self.rxdataArrayOffset] |= prevRxBit << self.rxdataIntOffset
                    self.rxdataIntOffset -= 1
                    if self.rxdataIntOffset < 0:
                        self.rxdataIntOffset = 31
                        self.rxdataArrayOffset += 1
                        self.rxData.append(0)
                    self.rxdataLen += 1
                    self.rxErrorDetect = False
                self.rxData[self.rxdataArrayOffset] |= rxBit << self.rxdataIntOffset
                self.rxdataIntOffset -= 1
                if self.rxdataIntOffset < 0:
                    self.rxdataIntOffset = 31
                    self.rxdataArrayOffset += 1
                    self.rxData.append(0)
                self.rxdataLen += 1
            else:
                # header search
                if self.rxErrorDetect:
                    if not (((self.rxHeaderMask & self.header) > 1) ^ (prevRxBit == 1)):  
                        self.rxHeaderMask = self.rxHeaderMask >> 1
                        if self.rxHeaderMask == 0:
                            self.rxHeaderFound = True
                    else:
                        self.rxHeaderMask = 0x80000000
                    self.rxErrorDetect = False

                if not (((self.rxHeaderMask & self.header) > 1) ^ (rxBit == 1)):  
                    self.rxHeaderMask = self.rxHeaderMask >> 1
                    if self.rxHeaderMask == 0:
                        self.rxHeaderFound = True
                        print 'Header Found\n'
                else:
                    self.rxHeaderMask = 0x80000000

    # returns the next bit to transmit
    def getNextSymbol(self):
        nextBits = -1

        if self.txdataLen > 0:
            # get next mask
            bitMask = 1<<self.txdataIntOffset 
            self.txdataIntOffset -= 1

            # get next bit
            nextBitRaw = 1 if bitMask & self.txData[self.txdataArrayOffset] > 0 else 0
            self.txdataLen -=1
            

            # reset for next int array
            if self.txdataIntOffset < 0:
                self.txdataIntOffset = 31
                self.txdataArrayOffset += 1


        if nextBit == 0x0:
            nextSymbol  = 0
        elif nextBit == 0x1:
            nextSymbol  = 1
        else:
            return 0

        return 0x80000000 >> self.txmask[nextSymbol]   



if __name__ == "__main__":
    txn = Node()
    txn.msgFunction[1](TxDataMessage([0xa50fa50f],32))
# header    
    txn.getNextRxBits([0x0004000])
    txn.getNextRxBits([0x0004000])
    txn.getNextRxBits([0x0008000])
    txn.getNextRxBits([0x0004000])

    txn.getNextRxBits([0x0004000])
    txn.getNextRxBits([0x0008000])
    txn.getNextRxBits([0x0004000])
    txn.getNextRxBits([0x0008000])
   
    txn.getNextRxBits([0x0004000])
    txn.getNextRxBits([0x0008000])
    txn.getNextRxBits([0x0008000])
    txn.getNextRxBits([0x0004000])

    txn.getNextRxBits([0x0004000])
    txn.getNextRxBits([0x0004000])
    txn.getNextRxBits([0x0004000])
    txn.getNextRxBits([0x0004000])

    txn.getNextRxBits([0x0008000])
    txn.getNextRxBits([0x0004000])
    txn.getNextRxBits([0x0008000])
    txn.getNextRxBits([0x0004000])

    txn.getNextRxBits([0x0008000])
    txn.getNextRxBits([0x0008000])
    txn.getNextRxBits([0x0004000])
    txn.getNextRxBits([0x0008000])
   
    txn.getNextRxBits([0x0008000])
    txn.getNextRxBits([0x0008000])
    txn.getNextRxBits([0x0004000])
    txn.getNextRxBits([0x0008000])

    txn.getNextRxBits([0x0004000])
    txn.getNextRxBits([0x0004000])
    txn.getNextRxBits([0x0008000])
    txn.getNextRxBits([0x0008000])


    txn.getNextRxBits([0x0008000])
    txn.getNextRxBits([0x0008000])
    txn.getNextRxBits([0x0008000])
    txn.getNextRxBits([0x0008000])

    txn.getNextRxBits([0x0008000])
    txn.getNextRxBits([0x0008000])
    txn.getNextRxBits([0x0008000])
    txn.getNextRxBits([0x0008000])
   
    txn.getNextRxBits([0x0008000])
    txn.getNextRxBits([0x0008000])
    txn.getNextRxBits([0x0004000])
    txn.getNextRxBits([0x0004000])

    txn.getNextRxBits([0x0008000])
    txn.getNextRxBits([0x0004000])
    txn.getNextRxBits([0x0004000])
    txn.getNextRxBits([0x0008000])

    txn.getNextRxBits([0x0008000])
    txn.getNextRxBits([0x0004000])
    txn.getNextRxBits([0x0004000])
    txn.getNextRxBits([0x0004000])

    txn.getNextRxBits([0x0008000])
    txn.getNextRxBits([0x0008000])
    txn.getNextRxBits([0x0004000])
    txn.getNextRxBits([0x0004000])
   
    txn.getNextRxBits([0x0004000])
    txn.getNextRxBits([0x0008000])
    txn.getNextRxBits([0x0004000])
    txn.getNextRxBits([0x0004000])

    txn.getNextRxBits([0x0004000])
    txn.getNextRxBits([0x0004000])
    txn.getNextRxBits([0x0004000])
    txn.getNextRxBits([0x0008000])
#
# data
#   txn.getNextRxBits([0x0008000])
#   txn.getNextRxBits([0x0004000])
#   txn.getNextRxBits([0x0008000])
#   txn.getNextRxBits([0x0004000])
#   txn.getNextRxBits([0x0004000])
#   txn.getNextRxBits([0x0008000])
#   txn.getNextRxBits([0x0004000])
#   txn.getNextRxBits([0x0008000])
#   txn.getNextRxBits([0x0004000])
#   txn.getNextRxBits([0x0004000])
#   txn.getNextRxBits([0x0004000])
#   txn.getNextRxBits([0x0004000])
#   txn.getNextRxBits([0x0008000])
#   txn.getNextRxBits([0x0008000])
#   txn.getNextRxBits([0x0008000])
#   txn.getNextRxBits([0x0008000])
#  print 'start of RX Data'
#   for n in txn.rxData:
#       print '%8x'%n
#    print 'end of rx data'
#   print '%x'%txn.getNextSymbol()
#   print '%x'%txn.getNextSymbol()
#   print '%x'%txn.getNextSymbol()
#   print '%x'%txn.getNextSymbol()
#   print ' ' 
#   print '%x'%txn.getNextSymbol()
#   print '%x'%txn.getNextSymbol()
#   print '%x'%txn.getNextSymbol()
#   print '%x'%txn.getNextSymbol()
#   print ' ' 
#   print '%x'%txn.getNextSymbol()
#   print '%x'%txn.getNextSymbol()
#   print '%x'%txn.getNextSymbol()
#   print '%x'%txn.getNextSymbol()
#   print ' ' 
#   print '%x'%txn.getNextSymbol()
#   print '%x'%txn.getNextSymbol()
#   print '%x'%txn.getNextSymbol()
#   print '%x'%txn.getNextSymbol()
#   print ' ' 
#   print '%x'%txn.getNextSymbol()
#   print '%x'%txn.getNextSymbol()
#   print '%x'%txn.getNextSymbol()
#   print '%x'%txn.getNextSymbol()
#   print ' ' 
#   print '%x'%txn.getNextSymbol()
#   print '%x'%txn.getNextSymbol()
#   print '%x'%txn.getNextSymbol()
#   print '%x'%txn.getNextSymbol()
#   print ' ' 
#   print '%x'%txn.getNextSymbol()
#   print '%x'%txn.getNextSymbol()
#   print '%x'%txn.getNextSymbol()
#   print '%x'%txn.getNextSymbol()
#   print ' ' 
#   print '%x'%txn.getNextSymbol()
#   print '%x'%txn.getNextSymbol()
#   print '%x'%txn.getNextSymbol()
#   print '%x'%txn.getNextSymbol()
#   print ' end of header ' 
#   print '%x'%txn.getNextSymbol()
#   print '%x'%txn.getNextSymbol()
#   print '%x'%txn.getNextSymbol()
#   print '%x'%txn.getNextSymbol()
#   print ' ' 
#   print '%x'%txn.getNextSymbol()
#   print '%x'%txn.getNextSymbol()
#   print '%x'%txn.getNextSymbol()
#   print '%x'%txn.getNextSymbol()
#   print ' ' 
#   print '%x'%txn.getNextSymbol()
#   print '%x'%txn.getNextSymbol()
#   print '%x'%txn.getNextSymbol()
#   print '%x'%txn.getNextSymbol()
#   print ' ' 
#   print '%x'%txn.getNextSymbol()
#   print '%x'%txn.getNextSymbol()
#   print '%x'%txn.getNextSymbol()
#   print '%x'%txn.getNextSymbol()
#   print ' ' 
#   print '%x'%txn.getNextSymbol()
#   print '%x'%txn.getNextSymbol()
#   print '%x'%txn.getNextSymbol()
#   print '%x'%txn.getNextSymbol()
#   print ' ' 
#   print '%x'%txn.getNextSymbol()
#   print '%x'%txn.getNextSymbol()
#   print '%x'%txn.getNextSymbol()
#   print '%x'%txn.getNextSymbol()
#   print ' ' 
#   print '%x'%txn.getNextSymbol()
#   print '%x'%txn.getNextSymbol()
#   print '%x'%txn.getNextSymbol()
#   print '%x'%txn.getNextSymbol()
#   print ' ' 
#   print '%x'%txn.getNextSymbol()
#   print '%x'%txn.getNextSymbol()
#   print '%x'%txn.getNextSymbol()
#   print '%x'%txn.getNextSymbol()
#   print ' ' 
