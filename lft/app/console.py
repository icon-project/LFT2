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
    from typing import Optional, Union
    from threading import Thread
    from IPython import embed
    from lft.event.mediators import DelayedEventMediator
    from lft.event.mediators.delayed_event_mediator import (DelayedEventInstantMediatorExecutor,
                                                            DelayedEventRecorderMediatorExecutor)

    class Console:
        def __init__(self, app: 'App'):
            self._app = app
            self._running = False
            self._queue = asyncio.Queue(1)
            self._loop: Optional[asyncio.AbstractEventLoop] = None

            self._thread = Thread(target=self._detect)
            self._listener = None

        def start(self):
            self._running = True
            self._loop = asyncio.get_event_loop()
            self._loop.create_task(self._execute())
            self._thread.start()

        def stop(self):
            self._running = False
            if self._listener:
                self._listener.stop()

        def _detect(self):
            with Listener(on_press=self._put) as listener:
                self._listener = listener
                listener.join()

        def _put(self, key: Key):
            async def _put_threadsafe():
                try:
                    await self._queue.put(key)
                except asyncio.QueueFull:
                    pass
            asyncio.run_coroutine_threadsafe(_put_threadsafe(), self._loop)

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
                Key.esc: self._handle_run_ipython
            }

        async def handle(self, key: Key, app: 'App'):
            try:
                handler = self._handlers[key]
            except KeyError:
                pass
            else:
                await handler(app)

        async def _handle_run_ipython(self, app: 'App'):
            loop = asyncio.get_event_loop()
            start_time = loop.time()

            try:
                embed(colors='Neutral')
            finally:
                for node in app.nodes:
                    mediator = node.event_system.get_mediator(DelayedEventMediator)
                    self._restore_delayed_mediator(start_time, mediator)

        def _restore_delayed_mediator(self,
                                      start_time: float,
                                      mediator: DelayedEventMediator):
            executor = mediator._executor
            if (not isinstance(executor, DelayedEventInstantMediatorExecutor) and
                    not isinstance(executor, DelayedEventRecorderMediatorExecutor)):
                return

            old_handlers = executor.handlers
            executor.handlers = set()

            for old_handler in old_handlers:
                old_handler.timer_handler.cancel()
                diff = old_handler.timer_handler.when() - start_time
                mediator.execute(diff, old_handler.event)
