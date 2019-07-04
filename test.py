import asyncio
from lft.event import EventSimulator
from lft.state import StateMachine, State


class IdleState(State):
    async def on_enter(self, event):
        print("Idle Enter", event)

    async def on_exit(self, event):
        print("Idle Exit", event)


class AttackState(State):
    async def on_enter(self, event):
        print("Attack Enter", event)

    async def on_exit(self, event):
        print("Attack Exit", event)


class RunState(State):
    async def on_enter(self, event):
        print("Run Enter", event)

    async def on_exit(self, event):
        print("Run Exit", event)


class Event0:
    def __init__(self, a):
        self.a = a

    def __str__(self):
        return f"Event0 {self.a}"


class Event1:
    def __init__(self, a, b):
        self.a = a
        self.b = b

    def __str__(self):
        return f"Event1 {self.a}, {self.b}"


idle_state = IdleState()
attack_state = AttackState()
run_state = RunState()

state_machine = StateMachine()
state_machine.add_state("idle", idle_state)
state_machine.add_state("attack", attack_state)
state_machine.add_state("run", run_state)

state_machine.add_transition("idle", "attack", Event0, lambda event0: event0.a == 1)
state_machine.add_transition("attack", "run", Event1, lambda event1: event1.a == 0 and event1.b == 0)
state_machine.add_transition("run", "idle", Event0, lambda event0: True)
state_machine.add_transition("run", "run", Event1, lambda event1: True)

state_machine.state = "idle"


async def main():
    event_system = EventSimulator()
    event_system.register_receiver(state_machine.transfer_states)

    asyncio.ensure_future(event_system.run_forever())

    await asyncio.sleep(1)
    event_system.raise_event(Event0(1))
    print()

    await asyncio.sleep(1)
    event_system.raise_event(Event1(0, 0))
    print()

    await asyncio.sleep(1)
    event_system.raise_event(Event0(1))
    event_system.raise_event(Event1(0, 0))
    event_system.raise_event(Event0(1))
    print()

asyncio.run(main())
