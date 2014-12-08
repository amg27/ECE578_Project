from multiprocessing import Process, Pipe
from controller import runControl 
from MessageClass import * 
from Node import Node
import random
from EveNode import *

class NodePair:
    def __init__(self,txnode,rxnode):
        self.txNode = txnode
        self.rxNode = rxnode
        self.ptx_conn, self.tx_conn = Pipe(True)
        self.prx_conn, self.rx_conn = Pipe(True)
        self.ptx = Process(target=self.txNode.runNode, args=(self.tx_conn,))
        self.prx = Process(target=self.rxNode.runNode, args=(self.rx_conn,))
        self.ptx.start()
        self.prx.start()

    def CompareResults(self):
        self.prx_conn.send(StatusMessage())
        passedB = False
        ba = StatusMessage()
        if self.prx_conn.poll(1):
            b = self.prx_conn.recv()#clear buffer
            print '%s checksums rx %x calc %x'%(self.rxNode.name, b.status[3], b.status[4])
            passedB = True
        if passedB :
            if b.status[3] == b.status[4]:
                return True
            else:
                return False
        else:
            print 'error found'

    def GetDisplayName(self):
        return self.txNode.name + ' to ' + self.rxNode.name

    def StopNodePair(self):
        self.ptx_conn.send(CloseMessage())
        self.prx_conn.send(CloseMessage())
        self.ptx.join()
        self.ptx_conn.close()
        self.tx_conn.close()
        self.ptx.terminate()
        self.prx.join()
        self.prx_conn.close()
        self.rx_conn.close()
        self.prx.terminate()

    def SetTranmitData(self,txData):
        self.ptx_conn.send(TxDataMessage(txData))
        if self.ptx_conn.poll(2):
            a = self.ptx_conn.recv()#clear buffer
            print 'inside checksum %x'%a.checksum
 
if __name__ == '__main__':

    clientPool = []
    nodePairs = []
    rc = runControl(5)
    
    # link number 1
    nodePairs.append(NodePair(Node(seed=1,name='tx1',header=0xf9a80f12,rtType=1,ss=True),
                              Node(seed=1,name='rx1',header=0xf9a80f12,rtType=0,ss=True))) 
    nodePairs.append(NodePair(Node(seed=7067,name='tx2',header=0xf9a80f12,rtType=1,ss=True),
                              Node(seed=7067,name='rx2',header=0xf9a80f12,rtType=0,ss=True))) 
    for np in nodePairs:
        clientPool.append(np.ptx_conn) 
        clientPool.append(np.prx_conn)
    print len(clientPool)

# set Transmit  Data 
    for np in nodePairs:
        arraySize = 16
        payload = arraySize*[None]
        for ii in range(arraySize):
            payload[ii] = random.randrange(0,255)
        np.SetTranmitData(payload)
        print payload 

    # open file to store symbol data
    fid = open('symbols','w')

    # Create Eve Node
    eveNode = EveNode()

    nextSymbol = [0]
    ndone = True
    countLoops = 0
    curTS = 0
    curSymbol = [0]
    while ndone:
        curSymbol = nextSymbol
        nextSymbol = [0]
        
        # pass Current Symbol in to EveNode
        eveNode.CompareOffset(curSymbol)

        # send current frame to all Rx/Tx nodes
        sm = SymbolMessage(curSymbol,ts=curTS)
        for con in clientPool:
            con.send(sm)
        
        # get Response from Rx/Tx nodes
        for con in clientPool:
            if con.poll(2):
                nextS = con.recv()
                if nextS.ty == 2:
                    nextSymbol[0] |= nextS.symbol
        fid.write('%4.0i : %s\n'%(curTS,format(nextSymbol[0],'064b'))) 
        

        curTS += 1
        countLoops += 1
        if countLoops >= 1340:
            ndone = False
    # end of while loop

   
    # report and kill node pairs
    for np in nodePairs:
        print '%s :%s'%(np.GetDisplayName(),'Passed' if np.CompareResults() else 'Failed')
        np.StopNodePair()
