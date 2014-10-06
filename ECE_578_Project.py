from multiprocessing import Process, Pipe
from controller import runControl 
from MessageClass import TxDataMessage, SymbolMessage
from txNode import TxNode




if __name__ == '__main__':
    rc = runControl(5)
    txNode1 = TxNode(4)

    ptx1_conn, tx1_conn = Pipe(True)
    ptx1 = Process(target=txNode1.runTxNode, args=(tx1_conn,))
    ptx1.start()
    ptx1_conn.send(TxDataMessage([0xa50fa50f],32))
    ptx1_conn.recv()
    nextSymbol = 0
    ndone = 1
    while ndone == 1:
    #print "%x"%(ptx1_conn.recv())
        curSymbol = nextSymbol
        ptx1_conn.send(SymbolMessage(curSymbol))
        nextS =  ptx1_conn.recv()
        nextSymbol = nextS.symbol
        print "%x"%(nextSymbol)
       
        # get tx status
        ptx1_conn.send(Message(6))
        tx1SatusMsg = ptx1_conn.recv()
        if tx1StatusMsg.status == 0:
            ndone = 0
    ptx1.join()
