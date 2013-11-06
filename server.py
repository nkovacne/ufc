from twisted.protocols import basic

class PolicyProtocol(basic.LineReceiver):
    delimiter = '\n'
    terminator = '\n\n'

    def __init__(self):
        self._buffer = []
    
    def lineReceived(self, line):
        if line:
            self._buffer.append(line)
        else:
            self._process_request()
            self._buffer = []

