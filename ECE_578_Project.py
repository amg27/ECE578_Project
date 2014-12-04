from multiprocessing import Process, Pipe
from controller import runControl 
from MessageClass import * 
from Node import Node


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
        if self.txNode.txChecksum == self.rxNode.rxChecksum:
            return True
        else:
            return False
    def GetDisplayName(self):
        return self.txNode.name + ' to ' + self.rxNode.name

    def StopNodePair(self):
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
        self.ptx_conn.recv()#clear buffer
 
if __name__ == '__main__':

    clientPool = []
    nodePairs = []
    rc = runControl(5)
    
    # link number 1
    nodePairs.append(NodePair(Node(seed=1,name='tx1',txmask=[0,1],rxmask=[16,17],header=0xf9a80f12),
                              Node(seed=1,name='rx1',rxmask=[0,1],txmask=[16,17],header=0xf9a80f12))) 
    nodePairs.append(NodePair(Node(seed=1,name='tx2',txmask=[2,3],rxmask=[4,5],header=0xf9a81f12),
                              Node(seed=1,name='rx2',rxmask=[2,3],txmask=[4,5],header=0xf9a81f12))) 
    for np in nodePairs:
        clientPool.append(np.ptx_conn) 
        clientPool.append(np.prx_conn)
    print len(clientPool)

# set Transmit  Data 
    nodePairs[0].SetTranmitData([0xa5,0x0f,0xa5,0x0f])
    nodePairs[1].SetTranmitData([0xa5,0x0f,0xa5,0x0f,0xa5,0x0f,0xa5,0x0f])
    
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
        if countLoops >= 340:
            ndone = False
    # end of while loop

    for con in clientPool:
        con.send(CloseMessage())
   
    # report and kill node pairs
    for np in nodePairs:
        print '%s :%s\n'%(np.GetDisplayName(),'Passed' if np.CompareResults() else 'Failed')
        np.StopNodePair()
