from multiprocessing import Process, Pipe
from MessageClass import * 
import zlib
import time
import datetime
import ctypes

def twos_comp(val,bits):
    if val < 0:
        val = val + 4294967296 
    return val

class Node:
    #The following function are for a switch case look up dictionary thing
    def TxData(self, msg):
        self.timeStamp = msg.timeStamp
        
        # reformat data to chars
        txBitLength = len(msg.data)
        charData = [None]*txBitLength
        index = 0
        for ii in msg.data:
            charData[index] = ctypes.c_int(ii).value&0xff
            index += 1
        
        # compure checksum
        self.txChecksum = zlib.crc32(''.join(chr(ii) for ii in charData) ,0xffff)
        self.fid.write('TX Checksum: %x\n'%self.txChecksum)
        if self.txChecksum < 0:
            self.txChecksum = twos_comp(self.txChecksum,32)
        self.fid.write('TX Checksum: %x\n'%self.txChecksum)

        # append checksum to transmit list
        txDataList = [self.header>>24, (self.header>>16)&0xff, (self.header>>8)&0xff,self.header&0xff] 
        txDataList += [txBitLength>>24, (txBitLength>>16)&0xff, (txBitLength>>8)&0xff,txBitLength&0xff]
        txDataList += charData  
        txDataList.append((ctypes.c_int(self.txChecksum).value>>24)&0xff)
        txDataList.append((ctypes.c_int(self.txChecksum).value>>16)&0xff)
        txDataList.append((ctypes.c_int(self.txChecksum).value>>8)&0xff)
        txDataList.append(ctypes.c_int(self.txChecksum).value&0xff)
#        print (txDataList)
        
        # encode with convolutional encoder
        d1 = False
        d2 = False
        bitLoc = 0x80
        charOff = 0
        outBitLoc = 7
        outCharOff = 0
        for ii in range(0,len(txDataList)*8):
            cb = txDataList[charOff] & bitLoc > 0
            b0 = d1 ^ d2 ^ cb
            b1 = d2 ^ cb

            d2 = d1
            d1 = cb

            bitLoc = bitLoc >> 1;
            if bitLoc == 0:
                bitLoc = 0x80
                charOff += 1
            
            self.txData[outCharOff] |= (1 if b0 else 0) << outBitLoc
            outBitLoc -= 1
            self.txData[outCharOff] |= (1 if b1 else 0) << outBitLoc
            outBitLoc -= 1
            if outBitLoc == -1:
                outBitLoc = 7 
                outCharOff += 1
                self.txData.append(0)
        # setup transmit params
        self.txdataLen = (outCharOff + 1) * 8 # for the header 
        self.txdataIntOffset = 7
        self.txdataArrayOffset = 0
        return TxDataMessage(self.txData,self.timeStamp, self.txChecksum)

    def Symbol(self, msg):
        self.timeStamp = msg.timeStamp
        #Rx msg proccessing
#       self.fid.write('rxSymbol %x\trxmask: %i\ttxmask: %i\n'%(msg.symbol[0],self.rxmask,self.txmask))
        if not self.timeStamp == 0:
            self.getNextRxBits(msg.symbol)

        # send next tx bit
        nmsg = SymbolMessage(self.getNextSymbol())
        self.GetNextChannel()
        return nmsg

    def Error(self, msg):
        self.timeStamp = msg.timeStamp
        self.error = 1
        return self.error

    def RxData(self, msg):
        return RxDataMessage(data=self.rxData,length=self.rxdataLen, ts=self.timeStamp)#, parity = zlib.crc32(self.rxData,'0xffff'))

#todo: include rx status
    def Status(self, msg):
        self.timeStamp = msg.timeStamp
        return StatusMessage([self.txdataLen, self.rxdataLen, self.txChecksum, self.rxChecksum, self.rxChecksumCalc])

    def Close(self, msg):
        # Dump RX Buffer
        self.fid.write('RX Buffer Rx len:%i\n'%self.rxBitLength)
        self.fid.write('RX len:%i\n'%self.rxdataLen)
        for ii in self.rxData:
            self.fid.write('%x\n'%ii)
        self.fid.write('file closed\n')
        self.fid.close()

    def openFile(self):
        timeText = datetime.datetime.fromtimestamp(time.time()).strftime('%H%M%S')
        filename = timeText+'_'+self.name
        #print filename
        self.fid = open(filename, 'w')
        self.fid.write('file-opened\n')

    def GetNextChannel(self):
        if self.ss:
            self.rxmask = self.txmask
            self.rxmask = self.txmask
            self.seed = (self.randA * self.seed + self.randB) % self.randC
            self.txmask = self.seed >> 10
        else:
            self.rxmask = 0
            self.txmask = 0


    # init fucntion       
    # mask[] is the index in the symbol array
    # mask[0] is 1 then data is 0
    # mask[1] is 1 then data is 1
    # header in 13bit barker code then link id then 11 bit barker code
    def __init__(self,name='New',seed=1, header=0xf9a80712,ss = False, rtType = 0):
        self.seed = seed
        self.ss = ss
        self.randA = 3527
        self.randB = 3541
        self.randC = 65536
        self.typeRxTx = rtType # 0 = rx node 1 = txnode
        self.txmask = 0
        self.rxmask = 0
        self.GetNextChannel()# set txmask

        self.curSymbol = 0
        self.header = header
        
        self.name = name
        self.fid = -1
        self.openFile()

        # Tx Variables
        self.txData = [0]
        self.txdataLen = 0
        self.txdataIntOffset = 7
        self.txdataArrayOffset = 0
        self.txChecksum = 0
        self.fid.write('------------------------------tx checksum set to 0 -----------------\n')
        # Receive Variables
        self.rxData = [0]
        self.rxdataIntOffset = 7
        self.rxdataArrayOffset = 0
        self.rxdataLen = 0
        self.rxMsgFound = False
        self.rxHeaderFound = False
        self.rxBuffer = 0
        self.rxBufferBit = True
        self.rxPrevState = 0
        self.rxHeaderMask = 0x80000000
        self.rxErrorDetect = False
        self.rxBitLengthMask = 31
        self.rxBitLength = 0
        self.rxMsgLengthFound = False
        self.rxChecksumMask = 31
        self.rxChecksum = 0;
        self.rxChecksumCalc = 0;
        self.rxChecksumFound = False


        self.timeStamp = 0

    # main running function    
    def runNode(self,conn):
        while conn.poll(2):
            incMsg = conn.recv()
            #self.fid.write('rx msg:%i\n'%incMsg.ty)
            retMsg = None
            if incMsg.ty == 1:
                retMsg = self.TxData(incMsg)
            elif incMsg.ty == 2:
                retMsg = self.Symbol(incMsg)
            elif incMsg.ty == 3:
                retMsg = None
            elif incMsg.ty == 4:
                retMsg = self.Error(incMsg)
            elif incMsg.ty == 5:
                retMsg = self.RxData(incMsg)
            elif incMsg.ty == 6:
                retMsg = self.Status(incMsg)
            elif incMsg.ty == 7:
                retMsg = self.Close(incMsg)

            conn.send(retMsg)
        conn.close()


    # receive next 2 bits 
    def getNextRxBits(self, symbol):
        mask = 0x8000000000000000 >> self.rxmask
#       self.fid.write('mask %x\n'%mask)
        # fix this if longer symbols are used
        if mask & symbol[0] >= 1:
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

            if self.rxErrorDetect and not self.rxChecksumFound:
                self.fid.write('Error Detected at %i\n'%self.timeStamp)
                self.HandleRxBit(prevRxBit)
            self.HandleRxBit(rxBit)
            return

    def HandleRxBit(self,curBit):
        # Synch Pattern Search
        if not self.rxHeaderFound:
            self.fid.write('Header Bit:%x\n'%curBit)
            if not (((self.rxHeaderMask & self.header) > 1) ^ (curBit == 1)):  
                self.rxHeaderMask = self.rxHeaderMask >> 1
                if self.rxHeaderMask == 0:
                    self.rxHeaderFound = True
                    #print 'Header Found\n'
                    self.fid.write('Header Found\n')
            else:
                self.rxHeaderMask = 0x80000000 
                self.fid.write('Header Rejected\n')
            return
        elif not self.rxMsgLengthFound:
            self.fid.write('Bit Len Bit:%x\n'%curBit)
            self.rxBitLength |= curBit << self.rxBitLengthMask
            self.rxBitLengthMask -= 1
            if self.rxBitLengthMask < 0:
                self.rxMsgLengthFound = True
                self.fid.write('RX Length found: %i\n'%self.rxBitLength)
                self.rxBitLength *=8
            return
        elif not self.rxMsgFound:
            self.fid.write('Msg Bit:%x\n'%curBit)
            self.rxData[self.rxdataArrayOffset] |= curBit << self.rxdataIntOffset
            self.rxdataIntOffset -= 1
            self.rxdataLen += 1
            if self.rxBitLength == self.rxdataLen: # end msg and create checksum if msg found
                self.rxMsgFound = True
                self.rxChecksumCalc = zlib.crc32(''.join(chr(ii) for ii in self.rxData) ,0xffff)
                if self.rxChecksumCalc < 0:
                    self.rxChecksumCalc = twos_comp(self.rxChecksumCalc,32)
                self.fid.write('RX Message Found with checksum %x\n'%self.rxChecksumCalc)
            if self.rxdataIntOffset < 0:
                self.rxdataIntOffset = 7
                self.rxdataArrayOffset += 1
                self.rxData.append(0)
            return
        elif not self.rxChecksumFound:
            self.fid.write('Checksum Bit:%x\n'%curBit)
            self.rxChecksum  |= curBit << self.rxChecksumMask 
            self.rxChecksumMask -= 1
            if self.rxChecksumMask < 0:
                self.rxChecksumFound = True
                self.fid.write('Checksum found: %x\n'%self.rxChecksum)
            return
        return

    # returns the next bit to transmit
    def getNextSymbol(self):
        nextBit = False

        if self.txdataLen > 0:
            # get next mask
            bitMask = 1<<self.txdataIntOffset 
            self.txdataIntOffset -= 1

            # get next bit
            nextBit = True if bitMask & self.txData[self.txdataArrayOffset] > 0 else False
#           self.fid.write('bitmask %x\ttxdata: %x\tnextBit: %i\ttxMask: %x\n'%(bitMask,self.txData[self.txdataArrayOffset],nextBit,self.txmask))
            self.txdataLen -=1
            

            # reset for next int array
            if self.txdataIntOffset < 0:
                self.txdataIntOffset = 7 
                self.txdataArrayOffset += 1

        nextSymbol = 0
        if nextBit:
            nextSymbol = 0x8000000000000000 >> self.txmask
#       self.fid.write('next tx symbol: %x\n'%nextSymbol)
        if self.typeRxTx == 0: # rx only
            return 0
        else:
            return nextSymbol


if __name__ == "__main__":
    txn = Node()
    
    txn.GetNextChannel()
    print txn.txmask
    print 'rx %i'%txn.rxmask
    txn.GetNextChannel()
    print txn.txmask
    print 'rx %i'%txn.rxmask
    txn.GetNextChannel()
    print txn.txmask
    print 'rx %i'%txn.rxmask
    txn.GetNextChannel()
    print txn.txmask
    print 'rx %i'%txn.rxmask

#    b = [0xa50fa50f]
#    print type(b[0])
    a = txn.TxData(TxDataMessage([0xa5, 0x0f, 0xa5, 0x0f],4*8))
    print '%x'%txn.txChecksum
#    for ii in a.data:
#        print '%x'%ii

    
        
# header    
    txn.getNextRxBits([0x80004000])
    txn.getNextRxBits([0x80004000])
    txn.getNextRxBits([0x00008000])
    txn.getNextRxBits([0x80004000])

    txn.getNextRxBits([0x80004000])
    txn.getNextRxBits([0x00008000])
    txn.getNextRxBits([0x80004000])
    txn.getNextRxBits([0x00008000])
   
    txn.getNextRxBits([0x80004000])
    txn.getNextRxBits([0x00008000])
    txn.getNextRxBits([0x00008000])
    txn.getNextRxBits([0x80004000])

    txn.getNextRxBits([0x80004000])
    txn.getNextRxBits([0x80004000])
    txn.getNextRxBits([0x80004000])
    txn.getNextRxBits([0x80004000])

    txn.getNextRxBits([0x00008000])
    txn.getNextRxBits([0x80004000])
    txn.getNextRxBits([0x00008000])
    txn.getNextRxBits([0x80004000])

    txn.getNextRxBits([0x00008000])
    txn.getNextRxBits([0x00008000])
    txn.getNextRxBits([0x80004000])
    txn.getNextRxBits([0x00008000])
   
    txn.getNextRxBits([0x00008000])
    txn.getNextRxBits([0x00008000])
    txn.getNextRxBits([0x80004000])
    txn.getNextRxBits([0x00008000])

    txn.getNextRxBits([0x80004000])
    txn.getNextRxBits([0x80004000])
    txn.getNextRxBits([0x00008000])
    txn.getNextRxBits([0x00008000])


    txn.getNextRxBits([0x00008000])
    txn.getNextRxBits([0x00008000])
    txn.getNextRxBits([0x00008000])
    txn.getNextRxBits([0x00008000])

    txn.getNextRxBits([0x00008000])
    txn.getNextRxBits([0x00008000])
    txn.getNextRxBits([0x00008000])
    txn.getNextRxBits([0x00008000])
   
    txn.getNextRxBits([0x00008000])
    txn.getNextRxBits([0x00008000])
    txn.getNextRxBits([0x80004000])
    txn.getNextRxBits([0x80004000])

    txn.getNextRxBits([0x00008000])
    txn.getNextRxBits([0x80004000])
    txn.getNextRxBits([0x80004000])
    txn.getNextRxBits([0x00008000])

    txn.getNextRxBits([0x00008000])
    txn.getNextRxBits([0x80004000])
    txn.getNextRxBits([0x80004000])
    txn.getNextRxBits([0x80004000])

    txn.getNextRxBits([0x00008000])
    txn.getNextRxBits([0x00008000])
    txn.getNextRxBits([0x80004000])
    txn.getNextRxBits([0x80004000])
   
    txn.getNextRxBits([0x80004000])
    txn.getNextRxBits([0x00008000])
    txn.getNextRxBits([0x80004000])
    txn.getNextRxBits([0x80004000])

    txn.getNextRxBits([0x80004000])
    txn.getNextRxBits([0x80004000])
    txn.getNextRxBits([0x80004000])
    txn.getNextRxBits([0x00008000])
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
    print 'start of RX Data'
    for n in txn.rxData:
        print '%8x'%n
    print 'end of rx data'
    print '%x'%txn.getNextSymbol()
    print '%x'%txn.getNextSymbol()
    print '%x'%txn.getNextSymbol()
    print '%x'%txn.getNextSymbol()
    print ' ' 
    print '%x'%txn.getNextSymbol()
    print '%x'%txn.getNextSymbol()
    print '%x'%txn.getNextSymbol()
    print '%x'%txn.getNextSymbol()
    print ' ' 
    print '%x'%txn.getNextSymbol()
    print '%x'%txn.getNextSymbol()
    print '%x'%txn.getNextSymbol()
    print '%x'%txn.getNextSymbol()
    print ' ' 
    print '%x'%txn.getNextSymbol()
    print '%x'%txn.getNextSymbol()
    print '%x'%txn.getNextSymbol()
    print '%x'%txn.getNextSymbol()
    print ' ' 
    print '%x'%txn.getNextSymbol()
    print '%x'%txn.getNextSymbol()
    print '%x'%txn.getNextSymbol()
    print '%x'%txn.getNextSymbol()
    print ' ' 
    print '%x'%txn.getNextSymbol()
    print '%x'%txn.getNextSymbol()
    print '%x'%txn.getNextSymbol()
    print '%x'%txn.getNextSymbol()
    print ' ' 
    print '%x'%txn.getNextSymbol()
    print '%x'%txn.getNextSymbol()
    print '%x'%txn.getNextSymbol()
    print '%x'%txn.getNextSymbol()
    print ' ' 
    print '%x'%txn.getNextSymbol()
    print '%x'%txn.getNextSymbol()
    print '%x'%txn.getNextSymbol()
    print '%x'%txn.getNextSymbol()
    print ' end of header ' 
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

