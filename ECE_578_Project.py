from multiprocessing import Process, Pipe
from controller import runControl 

def f(conn):
    conn.send(123)
    conn.close()





if __name__ == '__main__':
    rc = runControl(5)
    p_conn, c_conn = Pipe(True)
    p = Process(target=rc.runController, args=(c_conn,))
    p.start()
    p_conn.send(3)
    while p_conn.poll(2):
        print p_conn.recv()
    p.join()
