from multiprocessing import Process, Pipe
from controller import runControl 
from MessageClass import * 
from Node import Node
import random


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
        self.ptx_conn.send(StatusMessage())
        self.prx_conn.send(StatusMessage())
        passedA = False
        passedB = False
        if self.ptx_conn.poll(1):
            a = self.ptx_conn.recv()#clear buffer
            print '%s checksum %x'%(self.txNode.name, a.status[2])
            passedA = True
        if self.prx_conn.poll(1):
            b = self.prx_conn.recv()#clear buffer
            print '%s checksum %x'%(self.rxNode.name, a.status[3])
            passedB = True
        if passedB and passedA:
            if a.status[2] == b.status[3]:
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
    nodePairs.append(NodePair(Node(seed=1,name='tx1',header=0xf9a80f12),
                              Node(seed=1,name='rx1',header=0xf9a80f12))) 
    nodePairs.append(NodePair(Node(seed=2,name='tx2',header=0xf9a81f12),
                              Node(seed=2,name='rx2',header=0xf9a81f12))) 
    nodePairs.append(NodePair(Node(seed=3,name='tx3',header=0xf9a81f12),
                              Node(seed=3,name='rx3',header=0xf9a81f12))) 
    nodePairs.append(NodePair(Node(seed=4,name='tx4',header=0xf9a81f12),
                              Node(seed=4,name='rx4',header=0xf9a81f12))) 
    nodePairs.append(NodePair(Node(seed=5,name='tx5',header=0xf9a81f12),
                              Node(seed=5,name='rx5',header=0xf9a81f12))) 
    nodePairs.append(NodePair(Node(seed=6,name='tx6',header=0xf9a81f12),
                              Node(seed=6,name='rx6',header=0xf9a81f12))) 
    nodePairs.append(NodePair(Node(seed=7,name='tx7',header=0xf9a81f12),
                              Node(seed=7,name='rx7',header=0xf9a81f12))) 
    nodePairs.append(NodePair(Node(seed=8,name='tx8',header=0xf9a81f12),
                              Node(seed=8,name='rx8',header=0xf9a81f12))) 
    nodePairs.append(NodePair(Node(seed=9,name='tx9',header=0xf9a81f12),
                              Node(seed=9,name='rx9',header=0xf9a81f12))) 
    nodePairs.append(NodePair(Node(seed=10,name='tx10',header=0xf9a81f12),
                              Node(seed=10,name='rx10',header=0xf9a81f12))) 
    for np in nodePairs:
        clientPool.append(np.ptx_conn) 
        clientPool.append(np.prx_conn)
    print len(clientPool)

# set Transmit  Data 
    for np in nodePairs:
        payload = 4*[None]
        for ii in range(4):
            payload[ii] = random.randrange(0,255)
        np.SetTranmitData(payload)
    
    nextSymbol = [0]
    ndone = True
    countLoops = 0
    curTS = 0
    curSymbol = [0]
    while ndone:
        curSymbol = nextSymbol
        nextSymbol = [0]

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
#        print '%x'%nextSymbol[0] 
        

        curTS += 1
        countLoops += 1
        if countLoops >= 1340:
            ndone = False
    # end of while loop

   
    # report and kill node pairs
    for np in nodePairs:
        print '%s :%s'%(np.GetDisplayName(),'Passed' if np.CompareResults() else 'Failed')
        np.StopNodePair()
