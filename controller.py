from multiprocessing import Process, Pipe


class runControl:
    def __init__(self,sv=0):
        self.sv = sv

    def runController(self, conn):
        while conn.poll(2):
            a = conn.recv()
            self.sv += a
            conn.send(self.sv)
        conn.close()
