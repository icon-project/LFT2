import aiohttp
import base64
import json
import os
import pickle
from jsonrpcclient.clients.http_client import HTTPClient
from jsonrpcclient.clients.aiohttp_client import AiohttpClient
from typing import IO, Union
from lft.event import EventMediator, EventInstantMediatorExecutor, EventRecorder, EventReplayer
from lft.event import EventReplayerMediatorExecutor, EventRecorderMediatorExecutor


class JsonRpcEventInstantMediatorExecutor(EventInstantMediatorExecutor):
    def execute(self, url: str, method: str, params: dict=None):
        return request(url, method, **params)

    async def execute_async(self, url: str, method: str, params: dict=None):
        return await request_async(url, method, **params)


class JsonRpcEventRecorderMediatorExecutor(EventRecorderMediatorExecutor):
    def __init__(self, event_recorder: EventRecorder, io: IO):
        super().__init__(event_recorder)
        self._io = io
        self._number = 0

    def execute(self, url: str, method: str, params: dict=None):
        result = None
        try:
            result = request(url, method, params)
        except Exception as e:
            result = e
            raise e
        else:
            return result
        finally:
            self._write(result)

    async def execute_async(self, url: str, method: str, params: dict=None):
        result = None
        try:
            result = await request_async(url, method, params)
        except Exception as e:
            result = e
            raise e
        else:
            return result
        finally:
            self._write(result)

    def _write(self, result):
        number = self._event_recorder.number
        serialized = serialize(number, result)
        dumped = json.dumps(serialized)

        self._io.write(dumped)
        self._io.write(os.linesep)


class JsonRpcEventReplayerMediatorExecutor(EventReplayerMediatorExecutor):
    def __init__(self, event_replayer: EventReplayer, io: IO):
        super().__init__(event_replayer)
        self._io = io

    def execute(self, url: str, method: str, params: dict=None):
        last_number = None
        last_result = None

        while self._is_less_last_number(last_number):
            last_number, last_result = self._read()

        if not self._is_equal_last_number(last_number):
            raise RuntimeError

        if isinstance(last_result, Exception):
            raise last_result
        else:
            return last_result

    async def execute_async(self, url: str, method: str, params: dict=None):
        return self.execute(url, method, params)

    def _read(self):
        dumped = self._io.readline()
        if not dumped:
            return None, None
        if dumped == os.linesep:
            return None, None
        serialized = json.loads(dumped)
        return deserialize(serialized)

    def _is_less_last_number(self, last_number: int):
        return (
            last_number is None or
            last_number < self._event_replayer.number
        )

    def _is_equal_last_number(self, last_number: int):
        return (
            last_number is not None and
            last_number == self._event_replayer.number
        )


class JsonRpcEventMediator(EventMediator):
    InstantExecutorType = JsonRpcEventInstantMediatorExecutor
    RecorderExecutorType = JsonRpcEventRecorderMediatorExecutor
    ReplayerExecutorType = JsonRpcEventReplayerMediatorExecutor

    def execute(self, url: str, method: str, params: dict=None):
        return super().execute(url=url, method=method, params=params)

    async def execute_async(self, url: str, method: str, params: dict=None):
        return await super().execute_async(url=url, method=method, params=params)


def request(url: str, method: str, params: dict=None):
    if not params:
        params = {}
    client = HTTPClient(url)
    try:
        response = client.request(method, **params)
    except:
        raise
    else:
        return response.data.result


async def request_async(url: str, method: str, params: dict=None):
    if not params:
        params = {}

    async with aiohttp.ClientSession() as session:
        client = AiohttpClient(session, url)
        try:
            response = await client.request(method, **params)
        except:
            raise
        else:
            return response.data.result


def serialize(number, result: Union[dict, Exception]) -> dict:
    if isinstance(result, dict):
        return {
            "number": number,
            "type": "dict",
            "contents": result
        }
    if isinstance(result, Exception):
        pickle_dumped = pickle.dumps(result)
        base64_encoded = base64.encodebytes(pickle_dumped)
        utf8_decoded = base64_encoded.decode()
        return {
            "number": number,
            "type": "exception",
            "contents": utf8_decoded
        }
    raise TypeError(f"Undefined result type to serialize. Type({type(result)})")


def deserialize(serialized: dict) -> (int, Union[dict, Exception]):
    type_ = serialized["type"]
    if type_ == "dict":
        return serialized["number"], serialized["contents"]
    if type_ == "exception":
        utf8_decoded: str = serialized["contents"]
        base64_encoded = utf8_decoded.encode()
        pickle_dumped = base64.decodebytes(base64_encoded)
        return serialized["number"], pickle.loads(pickle_dumped)
    raise TypeError(f"Undefined result type to deserialize. Type({type_})")

