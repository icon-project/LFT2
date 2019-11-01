from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from lft.app import App

try:
    #  It is impossible to import it on running it out of terminal.
    from pynput.keyboard import Key, Listener
except:
    class Console:
        def __init__(self, app: 'App'):
            pass

        def start(self):
            pass

        def stop(self):
            pass
else:
    import asyncio
    from threading import Thread
    from IPython import embed

    class Console:
        def __init__(self, app: 'App'):
            self._app = app
            self._running = False
            self._queue = asyncio.Queue(1)

            self._thread = Thread(target=self._detect)
            self._listener = None

        def start(self):
            self._running = True
            self._thread.start()

            loop = asyncio.get_event_loop()
            loop.create_task(self._execute())

        def stop(self):
            self._running = False
            if self._listener:
                self._listener.stop()

        def _detect(self):
            def _queue(key):
                try:
                    self._queue.put_nowait(key)
                except asyncio.QueueFull:
                    pass

            with Listener(on_press=_queue) as listener:
                self._listener = listener
                listener.join()

        async def _execute(self):
            handler = Handler()
            while self._running:
                key = await self._queue.get()
                await handler.handle(key, self._app)

                try:
                    self._queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass


    class Handler:
        def __init__(self):
            self._handlers = {
                Key.esc: self._run_ipython
            }

        async def handle(self, key: Key, app: 'App'):
            try:
                handler = self._handlers[key]
            except KeyError:
                pass
            else:
                await handler(app)

        async def _run_ipython(self, app: 'App'):
            embed(colors='Neutral')
