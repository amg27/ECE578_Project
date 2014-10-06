class Message:
    def __init__(self,ty=0):
        self.ty = ty



class TxDataMessage(Message):
    def __init__(self,data=0,length=0):
        self.ty = 1
        self.data = data
        self.length = length

class StatusMessage(Message):
    def __init__(self, status):
        self.ty = 6
        self.status = status


class SymbolMessage(Message):
    def __init__(self,symbol):
        self.ty = 2
        self.symbol = symbol
