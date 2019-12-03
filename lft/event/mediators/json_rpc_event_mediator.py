import aiohttp
from jsonrpcclient.clients.http_client import HTTPClient
from jsonrpcclient.clients.aiohttp_client import AiohttpClient
from typing import IO
from lft.event import EventMediator, EventInstantMediatorExecutor, EventRecorder, EventReplayer
from lft.event import EventReplayerMediatorExecutor, EventRecorderMediatorExecutor
from lft.event.mediators.mixin import EventMediatorRecorderMixin

__all__ = ("JsonRpcEventMediator", "JsonRpcEventInstantMediatorExecutor",
           "JsonRpcEventRecorderMediatorExecutor", "JsonRpcEventReplayerMediatorExecutor")

class JsonRpcEventInstantMediatorExecutor(EventInstantMediatorExecutor):
    def execute(self, url: str, method: str, params: dict=None):
        return request(url, method, **params)

    async def execute_async(self, url: str, method: str, params: dict=None):
        return await request_async(url, method, **params)


class JsonRpcEventRecorderMediatorExecutor(EventRecorderMediatorExecutor, EventMediatorRecorderMixin):
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
            self._write(self._io, self._event_recorder.number, result)

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
            self._write(self._io, self._event_recorder.number, result)


class JsonRpcEventReplayerMediatorExecutor(EventReplayerMediatorExecutor, EventMediatorRecorderMixin):
    def __init__(self, event_replayer: EventReplayer, io: IO):
        super().__init__(event_replayer)
        self._io = io

    def execute(self, url: str, method: str, params: dict=None):
        result = self._read(self._io, self._event_replayer.number)

        if isinstance(result, Exception):
            raise result
        else:
            return result

    async def execute_async(self, url: str, method: str, params: dict=None):
        return self.execute(url, method, params)


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
