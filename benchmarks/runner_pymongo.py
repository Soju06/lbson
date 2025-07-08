from typing import Any

from runner import BSONModule, run


class PyMongoModule(BSONModule):
    def __init__(self) -> None:
        import bson

        self.encoder = bson.encode
        self.decoder = bson.decode

    def encode(self, data: dict[str, Any]) -> bytes:
        return self.encoder(data)

    def decode(self, data: bytes) -> dict[str, Any]:
        return self.decoder(data)


if __name__ == "__main__":
    run(PyMongoModule())
