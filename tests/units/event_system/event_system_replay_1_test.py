from io import StringIO
from typing import TypeVar
from lft.event import EventSystem
from lft.event.mediators import DelayedEventMediator, TimestampEventMediator, JsonRpcEventMediator
from tests.units.event_system import Event1, Event2, Event3

T = TypeVar("T")


def test_event_system():
    results = []

    event_system = EventSystem(use_priority=False)
    event_system.set_mediator(TimestampEventMediator)
    event_system.set_mediator(DelayedEventMediator)
    event_system.set_mediator(JsonRpcEventMediator)

    event_system.simulator.register_handler(Event1, lambda e: on_test1(e, results, event_system))
    event_system.simulator.register_handler(Event2, lambda e: on_test2(e, results, event_system))
    event_system.simulator.register_handler(Event3, lambda e: on_test3(e, results, event_system))

    record_io = StringIO()
    record_io.write(record)
    record_io.seek(0)

    timestamp_io = StringIO()
    timestamp_io.write(timestamp)
    timestamp_io.seek(0)

    json_rpc_io = StringIO()
    json_rpc_io.write(json_rpc)
    json_rpc_io.seek(0)

    event_system.start_replay(record_io, {TimestampEventMediator: timestamp_io, JsonRpcEventMediator: json_rpc_io})


record = r"""
{"!type": "lft.event.event_recorder.EventRecord", "!data": {"number": 0, "event": {"!type": "tests.event_system.event_system_replay_0_test.Event1", "!data": {}}}}
{"!type": "lft.event.event_recorder.EventRecord", "!data": {"number": 2, "event": {"!type": "tests.event_system.event_system_replay_0_test.Event3", "!data": {"num": 3}}}}
"""

timestamp = r"""
{"!number": 1, "!type": "int", "!data": 1564560247454275}
{"!number": 1, "!type": "int", "!data": 1564560247454501}
{"!number": 2, "!type": "int", "!data": 1564560250967674}
{"!number": 3, "!type": "int", "!data": 1564560254034700}
"""

json_rpc = r"""
{"!number": 1, "!type": "exception", "!data": "gANjanNvbnJwY2NsaWVudC5leGNlcHRpb25zClJlY2VpdmVkTm9uMnh4UmVzcG9uc2VFcnJvcgpx\nAFgYAAAAUmVjZWl2ZWQgNDAwIHN0YXR1cyBjb2RlcQGFcQJScQN9cQRYBAAAAGNvZGVxBU2QAXNi\nLg==\n"}
{"!number": 1, "!type": "exception", "!data": "gANjcmVxdWVzdHMuZXhjZXB0aW9ucwpDb25uZWN0aW9uRXJyb3IKcQBjdXJsbGliMy5leGNlcHRp\nb25zCk1heFJldHJ5RXJyb3IKcQFOWAcAAAAvYXBpL3YzcQJOh3EDUnEEhXEFUnEGfXEHKFgIAAAA\ncmVzcG9uc2VxCE5YBwAAAHJlcXVlc3RxCWNyZXF1ZXN0cy5tb2RlbHMKUHJlcGFyZWRSZXF1ZXN0\nCnEKKYFxC31xDChYBgAAAG1ldGhvZHENWAQAAABQT1NUcQ5YAwAAAHVybHEPWCcAAABodHRwczov\nL3dhbGxldC5pY29uLmZvdW5kYXRpb24xbC9hcGkvdjNxEFgHAAAAaGVhZGVyc3ERY3JlcXVlc3Rz\nLnN0cnVjdHVyZXMKQ2FzZUluc2Vuc2l0aXZlRGljdApxEimBcRN9cRRYBgAAAF9zdG9yZXEVY2Nv\nbGxlY3Rpb25zCk9yZGVyZWREaWN0CnEWKVJxFyhYCgAAAHVzZXItYWdlbnRxGFgKAAAAVXNlci1B\nZ2VudHEZWBYAAABweXRob24tcmVxdWVzdHMvMi4yMC4wcRqGcRtYDwAAAGFjY2VwdC1lbmNvZGlu\nZ3EcWA8AAABBY2NlcHQtRW5jb2RpbmdxHVgNAAAAZ3ppcCwgZGVmbGF0ZXEehnEfWAYAAABhY2Nl\ncHRxIFgGAAAAQWNjZXB0cSFYEAAAAGFwcGxpY2F0aW9uL2pzb25xIoZxI1gKAAAAY29ubmVjdGlv\nbnEkWAoAAABDb25uZWN0aW9ucSVYCgAAAGtlZXAtYWxpdmVxJoZxJ1gMAAAAY29udGVudC10eXBl\ncShYDAAAAENvbnRlbnQtVHlwZXEpaCKGcSpYDgAAAGNvbnRlbnQtbGVuZ3RocStYDgAAAENvbnRl\nbnQtTGVuZ3RocSxYAgAAADU3cS2GcS51c2JYCAAAAF9jb29raWVzcS9jcmVxdWVzdHMuY29va2ll\ncwpSZXF1ZXN0c0Nvb2tpZUphcgpxMCmBcTF9cTIoWAcAAABfcG9saWN5cTNjaHR0cC5jb29raWVq\nYXIKRGVmYXVsdENvb2tpZVBvbGljeQpxNCmBcTV9cTYoWAgAAABuZXRzY2FwZXE3iFgHAAAAcmZj\nMjk2NXE4iVgTAAAAcmZjMjEwOV9hc19uZXRzY2FwZXE5TlgMAAAAaGlkZV9jb29raWUycTqJWA0A\nAABzdHJpY3RfZG9tYWlucTuJWBsAAABzdHJpY3RfcmZjMjk2NV91bnZlcmlmaWFibGVxPIhYFgAA\nAHN0cmljdF9uc191bnZlcmlmaWFibGVxPYlYEAAAAHN0cmljdF9uc19kb21haW5xPksAWBwAAABz\ndHJpY3RfbnNfc2V0X2luaXRpYWxfZG9sbGFycT+JWBIAAABzdHJpY3RfbnNfc2V0X3BhdGhxQIlY\nEAAAAF9ibG9ja2VkX2RvbWFpbnNxQSlYEAAAAF9hbGxvd2VkX2RvbWFpbnNxQk5YBAAAAF9ub3dx\nQ0p6S0FddWJoL31xRGhDSnpLQV11YlgEAAAAYm9keXFFQzl7Impzb25ycGMiOiAiMi4wIiwgIm1l\ndGhvZCI6ICJpY3hfZ2V0TGFzdEJsb2NrIiwgImlkIjogMX1xRlgFAAAAaG9va3NxR31xSGgIXXFJ\nc1gOAAAAX2JvZHlfcG9zaXRpb25xSk51YnViLg==\n"}
{"!number": 2, "!type": "dict", "!data": {"version": "0.1a", "prev_block_hash": "dae35ec99b918d66745c3529ad2c6cb684b36e8b0f23d4dead64951ebe1ba16f", "merkle_tree_root_hash": "ca0e9e1476c1add1f9fb74cfa15c1129406816baa4efa07ddeae83158890e3e0", "time_stamp": 1564560247863015, "confirmed_transaction_list": [{"version": "0x3", "from": "hxa9546e6e6ec8bcb1e52106914f5f1fba90013f44", "to": "cx1b97c1abfd001d5cd0b5a3f93f22cccfea77e34e", "timestamp": "0x58ef591274190", "nid": "0x1", "stepLimit": "0x2625a00", "dataType": "call", "value": "0x68155a43676e00000", "data": {"method": "bet_on_numbers", "params": {"numbers": "7,8,9,10,11,12,13,14,15,16,17,18,19,20", "user_seed": ""}}, "signature": "wa+chZN4cuBewZGsVYBJQjzbMB/As+C0kByGt1KW3H1HYrxNxUPwV0RGQK5Gt5obJpTxv7EDa1Tx2jEnahKqbwA=", "txHash": "0xca0e9e1476c1add1f9fb74cfa15c1129406816baa4efa07ddeae83158890e3e0"}], "block_hash": "5b56f64bb4598746b65edeb64638e41b9707fe7dbd6b59bde3e1d4c6c155297a", "height": 6486306, "peer_id": "hx04fb8e539e0cafe69cbf114c973334bf9a58cec7", "signature": "GF1xENEPi77rqEnzOdNZrhhNAOtyrmSeMEG+YAmFk5YYmUjHDMZ1f1Ar1rLlMnGbG4z7i8ptpLqmdf3TuN00kgA=", "next_leader": "hx04fb8e539e0cafe69cbf114c973334bf9a58cec7"}}
{"!number": 3, "!type": "dict", "!data": {"version": "0.1a", "prev_block_hash": "d4d262a83b6a759a3414aa8079c81a1c9d7659ad6bf1bcf02b8ed90910134bf0", "merkle_tree_root_hash": "2a9875f88da7ec8d3f7cd75eea5503a3259655f94b96af9de4a05349a1fa054e", "time_stamp": 1564560251863533, "confirmed_transaction_list": [{"version": "0x3", "from": "hxedddc5504e3809fd3d796e2148c9217a8d6c2ae1", "to": "cx1b97c1abfd001d5cd0b5a3f93f22cccfea77e34e", "timestamp": "0x58ef591e06030", "nid": "0x1", "stepLimit": "0x2625a00", "dataType": "call", "value": "0x8ac7230489e80000", "data": {"method": "bet_on_numbers", "params": {"numbers": "1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20", "user_seed": ""}}, "signature": "eLT3UJ4qKY/DxG1+cG9LKdxKezyKFFobavdd2CGY6VpCCSLDTTFf4iIt2GvHBUC7zrwWZnMK+dtLiOmoIrOd5wA=", "txHash": "0x2a9875f88da7ec8d3f7cd75eea5503a3259655f94b96af9de4a05349a1fa054e"}], "block_hash": "9ef90ffc63ae9a9c6258edf07c66bbfb0d80a30e14457187a95ebab8e93422ae", "height": 6486308, "peer_id": "hx04fb8e539e0cafe69cbf114c973334bf9a58cec7", "signature": "cSjNWdTJi0LmGqP+SviSbVdXP+BLF12VHGxdQ5VNM81cJ+en4rg9EGBWzwbxqrd/vLzG3dGLhmqrBZE6KXsr1wE=", "next_leader": "hx04fb8e539e0cafe69cbf114c973334bf9a58cec7"}}
"""


if __name__ == "__main__":
    test_event_system()
