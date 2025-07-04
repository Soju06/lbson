from __future__ import annotations
import typing
__all__ = ['DecoderMode', 'decode', 'encode']
class DecoderMode:
    """
    Members:
    
      JSON
    
      EXTENDED_JSON
    
      PYTHON
    """
    EXTENDED_JSON: typing.ClassVar[DecoderMode]  # value = <DecoderMode.EXTENDED_JSON: 1>
    JSON: typing.ClassVar[DecoderMode]  # value = <DecoderMode.JSON: 0>
    PYTHON: typing.ClassVar[DecoderMode]  # value = <DecoderMode.PYTHON: 2>
    __members__: typing.ClassVar[dict[str, DecoderMode]]  # value = {'JSON': <DecoderMode.JSON: 0>, 'EXTENDED_JSON': <DecoderMode.EXTENDED_JSON: 1>, 'PYTHON': <DecoderMode.PYTHON: 2>}
    def __eq__(self, other: typing.Any) -> bool:
        ...
    def __getstate__(self) -> int:
        ...
    def __hash__(self) -> int:
        ...
    def __index__(self) -> int:
        ...
    def __init__(self, value: int) -> None:
        ...
    def __int__(self) -> int:
        ...
    def __ne__(self, other: typing.Any) -> bool:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, state: int) -> None:
        ...
    def __str__(self) -> str:
        ...
    @property
    def name(self) -> str:
        ...
    @property
    def value(self) -> int:
        ...
def decode(data: bytes, *, mode: DecoderMode = DecoderMode.PYTHON, max_depth: int = 2147483647) -> dict:
    ...
def encode(obj: typing.Any, *, skipkeys: bool = False, check_circular: bool = True, allow_nan: bool = True, sort_keys: bool = False, max_depth: int = 2147483647, max_size: int = 2147483647) -> bytes:
    ...
__version__: str = '0.1.0'
