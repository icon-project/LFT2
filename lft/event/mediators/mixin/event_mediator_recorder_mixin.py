import base64
import json
import os
import pickle
from typing import Any, IO

__all__ = ("EventMediatorRecorderMixin")


class EventMediatorRecorderMixin:
    def _write(self, io: IO, number: int, result: Any):
        serialized = self._serialize(number, result)
        dumped = json.dumps(serialized)

        io.write(dumped)
        io.write(os.linesep)

    def _serialize(self, number: int, result: Any):
        if isinstance(result, Exception):
            type_ = "exception"
            pickle_dumped = pickle.dumps(result)
            base64_encoded = base64.encodebytes(pickle_dumped)
            data = base64_encoded.decode()
        else:
            type_ = str(type(result).__qualname__)
            data = result

        return {
            "!number": number,
            "!type": type_,
            "!data": data
        }

    def _read(self, io: IO, number: int) -> Any:
        cur_number = -1
        cur_result = None

        while cur_number < number:
            cur_number, cur_result = self._readline(io)

        if cur_number != number:
            raise RuntimeError(f"Cannot find proper number. {number} / {cur_number}")
        return cur_result

    def _readline(self, io: IO):
        dumped = io.readline()
        if not dumped:
            return -1, None
        if dumped == os.linesep:
            return -1, None
        serialized = json.loads(dumped)
        return self._deserialize(serialized)

    def _deserialize(self, serialized: dict) -> (int, Any):
        if serialized["!type"] == "exception":
            utf8_decoded: str = serialized["!data"]
            base64_encoded = utf8_decoded.encode()
            pickle_dumped = base64.decodebytes(base64_encoded)
            contents = pickle.loads(pickle_dumped)
        else:
            contents = serialized["!data"]
        return serialized["!number"], contents
