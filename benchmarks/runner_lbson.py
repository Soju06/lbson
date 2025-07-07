from runner import BSONModule, run


class LbsonModule(BSONModule):
    def __init__(self) -> None:
        import lbson

        self.encoder = lbson.encode
        self.decoder = lbson.decode

    def encode(self, data: dict) -> bytes:
        # A little trick like the check_circular flag is fine, right?
        return self.encoder(data, check_circular=False)

    def decode(self, data: bytes) -> dict:
        return self.decoder(data)


if __name__ == "__main__":
    run(LbsonModule())
