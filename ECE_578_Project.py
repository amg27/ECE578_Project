from multiprocessing import Process, Pipe
from controller import runControl 
from MessageClass import * 
from txNode import TxNode


curSymbol = 0

clientPool = []


if __name__ == '__main__':
    global curSymbol
    global clientPool

    rc = runControl(5)
    
    txNode1 = TxNode(seed=1,mask=[0,1,2,3])
    txNode2 = TxNode(seed=2,mask=[4,5,6,7])
    txNode3 = TxNode(seed=3,mask=[8,9,10,11])
    txNode4 = TxNode(seed=4,mask=[12,13,14,15])

    ptx1_conn, tx1_conn = Pipe(True)
    ptx2_conn, tx2_conn = Pipe(True)
    ptx3_conn, tx3_conn = Pipe(True)
    ptx4_conn, tx4_conn = Pipe(True)
    
    
    
    ptx1 = Process(target=txNode1.runTxNode, args=(tx1_conn,))
    ptx2 = Process(target=txNode2.runTxNode, args=(tx2_conn,))
    ptx3 = Process(target=txNode3.runTxNode, args=(tx3_conn,))
    ptx4 = Process(target=txNode4.runTxNode, args=(tx4_conn,))
    ptx1.start()
    ptx2.start()
    ptx3.start()
    ptx4.start()

    clientPool.append(ptx1_conn)
    clientPool.append(ptx2_conn)
    clientPool.append(ptx3_conn)
    clientPool.append(ptx4_conn)

    ptx1_conn.send(TxDataMessage([0xa50fa50f],32))
    ptx2_conn.send(TxDataMessage([0xa50fa50f],32))
    ptx3_conn.send(TxDataMessage([0xa50fa50f],32))
    ptx4_conn.send(TxDataMessage([0xa50fa50f],32))
    ptx1_conn.recv()
    ptx2_conn.recv()
    ptx3_conn.recv()
    ptx4_conn.recv()
    
    nextSymbol = 0
    ndone = 1
    countLoops = 0
    while ndone == 1:
        curSymbol = nextSymbol
        nextSymbol = 0

        # send current frame to all Rx/Tx nodes
        sm = SymbolMessage(curSymbol)
        for con in clientPool:
            con.send(sm)
        
        # get Response from Rx/Tx nodes
        for con in clientPool:
            if con.poll(2):
                nextS = con.recv()
                if nextS.ty == 2:
                    nextSymbol |= nextS.symbol
               # else:    
                    

        print "%8x"%(nextSymbol)
       
        # get tx status
        ptx1_conn.send(Message(6))
        if ptx1_conn.poll(1):
            tx1StatusMsg = ptx1_conn.recv()
            countLoops += 1
            #if tx1StatusMsg.status == 0 or countLoops == 20:
            if countLoops == 20:
                ndone = 0
        else:
            ndone = 0
    ptx1.join()
    ptx1_conn.close()
    tx1_conn.close()
    ptx1.terminate()
