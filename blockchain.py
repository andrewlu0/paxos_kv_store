from block import Block


class Blockchain:
    def __init__(self):
        self.chain = []
    
    def append(self, block):
        self.chain.append(block)
    
    def clear(self):
        self.chain = []

    def last(self):
        if not self.chain:
            return None
        return self.chain[-1]

    def __str__(self):
        block_str = []
        for block in self.chain:
          block_str.append(str(block))
        return str(block_str)
