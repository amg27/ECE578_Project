from multiprocessing import Process, Pipe
from controller import runControl 
from MessageClass import * 
from Node import Node


curSymbol = 0

clientPool = []


if __name__ == '__main__':
#    global curSymbol
#    global clientPool

    rc = runControl(5)
    
    # link number 1
    txNode1 = Node(seed=1,name='tx1',txmask=[0,1],rxmask=[16,17],header=0xf9a80f12)
    # link number 10
#    txNode2 = Node(seed=2,txmask=[4,5],rxmask=[20,21],header=0xf9a85f12)
    # link number 100
#    txNode3 = Node(seed=3,txmask=[8,9],rxmask=[24,25],header=0xf9ab2712)
    # link number 200
#    txNode4 = Node(seed=4,txmask=[12,13],rxmask=[28,29],header=0xf9ae4712)


    # link number 1
    rxNode1 = Node(seed=1,name='rx1',rxmask=[0,1],txmask=[16,17],header=0xf9a80f12)
    # link number 10
#    rxNode2 = Node(seed=2,rxmask=[4,5],txmask=[20,21],header=0xf9a85f12)
    # link number 100
#    rxNode3 = Node(seed=3,rxmask=[8,9],txmask=[24,25],header=0xf9ab2712)
    # link number 200
#    rxNode4 = Node(seed=4,rxmask=[12,13],txmask=[28,29],header=0xf9ae4712)

    
    
    
    ptx1_conn, tx1_conn = Pipe(True)
#    ptx2_conn, tx2_conn = Pipe(True)
#    ptx3_conn, tx3_conn = Pipe(True)
#    ptx4_conn, tx4_conn = Pipe(True)
    
    
    prx1_conn, rx1_conn = Pipe(True)
#    prx2_conn, rx2_conn = Pipe(True)
#    prx3_conn, rx3_conn = Pipe(True)
#    prx4_conn, rx4_conn = Pipe(True)
    
    ptx1 = Process(target=txNode1.runNode, args=(tx1_conn,))
#    ptx2 = Process(target=txNode2.runNode, args=(tx2_conn,))
#    ptx3 = Process(target=txNode3.runNode, args=(tx3_conn,))
#    ptx4 = Process(target=txNode4.runNode, args=(tx4_conn,))
    prx1 = Process(target=rxNode1.runNode, args=(rx1_conn,))
#    prx2 = Process(target=rxNode2.runNode, args=(rx2_conn,))
#    prx3 = Process(target=rxNode3.runNode, args=(rx3_conn,))
#    prx4 = Process(target=rxNode4.runNode, args=(rx4_conn,))
    ptx1.start()
#    ptx2.start()
#    ptx3.start()
#    ptx4.start()
    prx1.start()
#    prx2.start()
#    prx3.start()
#    prx4.start()

    clientPool.append(ptx1_conn)
 #   clientPool.append(ptx2_conn)
#    clientPool.append(ptx3_conn)
#    clientPool.append(ptx4_conn)
    clientPool.append(prx1_conn)
#    clientPool.append(prx2_conn)
#    clientPool.append(prx3_conn)
#    clientPool.append(prx4_conn)

    ptx1_conn.send(TxDataMessage([0xa5,0x0f,0xa5,0x0f],32))
#    ptx2_conn.send(TxDataMessage([0xa50fa50f],32))
#    ptx3_conn.send(TxDataMessage([0xa50fa50f],32))
#    ptx4_conn.send(TxDataMessage([0xa50fa50f],32))
    ptx1_conn.recv()
#    ptx2_conn.recv()
#    ptx3_conn.recv()
#    ptx4_conn.recv()
    
    nextSymbol = [0]
    ndone = 1
    countLoops = 0
    curTS = 0
    curSymbol = [0]
    while ndone == 1:
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
               # else:    
                    

        print "%8x"%(nextSymbol[0])
        
       
        # get tx status
        ptx1_conn.send(StatusMessage(curTS))
        curTS += 1
        if ptx1_conn.poll(1):
            tx1StatusMsg = ptx1_conn.recv()
            countLoops += 1
            #if tx1StatusMsg.status == 0 or countLoops == 20:
            if countLoops == 340:
                ndone = 0
        else:
            ndone = 0

    # get rx messages       
    print 'rx data'
    for con in clientPool:
        con.send(RQRxDataMessage())
    for con in clientPool:
        if con.poll(2):
            smsg = con.recv()
            for ii in smsg.data:
                tempData = ii << 2
                print '%8x'%tempData
    for con in clientPool:
        con.send(CloseMessage())

    ptx1.join()
    ptx1_conn.close()
    tx1_conn.close()
    ptx1.terminate()
