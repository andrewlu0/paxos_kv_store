class Operation:
    def __init__(self, op=None, key=None, value=None):
        self.op = op
        self.key = key
        self.value = value
    
    def is_empty(self):
        return not self.op and not self.key and not self.value
    
    def to_dict(self):
        return {
            "op": self.op,
            "key": self.key,
            "value": self.value
        }

    def __str__(self):
        return "%s %s %s" % (self.op, self.key, str(self.value))

class Block:
    def __init__(self, operation=Operation(), nonce=None, hash=None):
        self.operation = operation
        self.nonce = nonce
        self.hash = hash

    def is_empty(self):
        return self.operation.is_empty() and not self.nonce and not self.hash

    def to_dict(self):
        return {
            "operation": self.operation.to_dict(),
            "nonce": self.nonce,
            "hash": self.hash
        }

    def __str__(self):
        return "%s %s %s" % (str(self.operation), self.nonce, self.hash)