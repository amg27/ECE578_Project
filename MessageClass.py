# carries data to be transmitted without delay
class TxDataMessage():
    def __init__(self,data=0,length=0, ts=0):
        self.ty = 1
        self.data = data
        self.length = length
        self.timeStamp = ts

# Carries data received by the node, only after rx data is received 
class RxDataMessage():
    def __init__(self,data=0,length=0, ts=0, cs=-1):
        self.ty = 1
        self.data = data
        self.length = length
        self.timeStamp = ts
        self.checksum = cs # 0 = pass

class StatusMessage():
    def __init__(self, status, ts=0):
        self.ty = 6
        self.status = status
        self.timeStamp = ts


class SymbolMessage():
    def __init__(self,symbol, ts=0):
        self.ty = 2
        self.symbol = symbol
        self.timeStamp = ts



if __name__ == "__main__":
    t = SymbolMessage(3,456)
    print t.timeStamp
