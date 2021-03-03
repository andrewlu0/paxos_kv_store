class Block:
    def __init__(self, op=tuple(), nonce="", hash=""):
        self.op = op
        self.nonce = nonce
        self.hash = hash

    def to_dict(self):
        return {"operation": self.op, "nonce": self.nonce, "hash": self.hash}

    def __str__(self):
        return "{ operation: %s, nonce: %s, hash: %s }" % (
            self.op,
            self.nonce,
            self.hash,
        )
