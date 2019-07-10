from io import StringIO
from typing import TypeVar
from lft.event import EventSystem
from lft.event.mediators import DelayedEventMediator, TimestampEventMediator, JsonRpcEventMediator
from tests.event_system.event_system_replay_0_test import Event1, Event2, Event3, on_test1, on_test2, on_test3

T = TypeVar("T")


def test_event_system():
    results = []

    event_system = EventSystem(False)
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
{"number": 0, "event": {"event_name": "tests.event_system.event_system_replay_0_test.Event1", "event_contents": {}}}
{"number": 2, "event": {"event_name": "tests.event_system.event_system_replay_0_test.Event3", "event_contents": {"num": 3}}}
"""

timestamp = r"""
{"number": 1, "type": "int", "contents": 1562570860521752}
{"number": 1, "type": "int", "contents": 1562570860521947}
{"number": 2, "type": "int", "contents": 1562570860695386}
{"number": 3, "type": "int", "contents": 1562570863808278}
"""

json_rpc = r"""
{"number": 1, "type": "exception", "contents": "gANjanNvbnJwY2NsaWVudC5leGNlcHRpb25zClJlY2VpdmVkTm9uMnh4UmVzcG9uc2VFcnJvcgpx\nAFgYAAAAUmVjZWl2ZWQgNDAwIHN0YXR1cyBjb2RlcQGFcQJScQN9cQRYBAAAAGNvZGVxBU2QAXNi\nLg==\n"}
{"number": 1, "type": "exception", "contents": "gANjcmVxdWVzdHMuZXhjZXB0aW9ucwpDb25uZWN0aW9uRXJyb3IKcQBjdXJsbGliMy5leGNlcHRp\nb25zCk1heFJldHJ5RXJyb3IKcQFOWAcAAAAvYXBpL3YzcQJOh3EDUnEEhXEFUnEGfXEHKFgIAAAA\ncmVzcG9uc2VxCE5YBwAAAHJlcXVlc3RxCWNyZXF1ZXN0cy5tb2RlbHMKUHJlcGFyZWRSZXF1ZXN0\nCnEKKYFxC31xDChYBgAAAG1ldGhvZHENWAQAAABQT1NUcQ5YAwAAAHVybHEPWCcAAABodHRwczov\nL3dhbGxldC5pY29uLmZvdW5kYXRpb24xbC9hcGkvdjNxEFgHAAAAaGVhZGVyc3ERY3JlcXVlc3Rz\nLnN0cnVjdHVyZXMKQ2FzZUluc2Vuc2l0aXZlRGljdApxEimBcRN9cRRYBgAAAF9zdG9yZXEVY2Nv\nbGxlY3Rpb25zCk9yZGVyZWREaWN0CnEWKVJxFyhYCgAAAHVzZXItYWdlbnRxGFgKAAAAVXNlci1B\nZ2VudHEZWBYAAABweXRob24tcmVxdWVzdHMvMi4yMC4wcRqGcRtYDwAAAGFjY2VwdC1lbmNvZGlu\nZ3EcWA8AAABBY2NlcHQtRW5jb2RpbmdxHVgNAAAAZ3ppcCwgZGVmbGF0ZXEehnEfWAYAAABhY2Nl\ncHRxIFgGAAAAQWNjZXB0cSFYEAAAAGFwcGxpY2F0aW9uL2pzb25xIoZxI1gKAAAAY29ubmVjdGlv\nbnEkWAoAAABDb25uZWN0aW9ucSVYCgAAAGtlZXAtYWxpdmVxJoZxJ1gMAAAAY29udGVudC10eXBl\ncShYDAAAAENvbnRlbnQtVHlwZXEpaCKGcSpYDgAAAGNvbnRlbnQtbGVuZ3RocStYDgAAAENvbnRl\nbnQtTGVuZ3RocSxYAgAAADU3cS2GcS51c2JYCAAAAF9jb29raWVzcS9jcmVxdWVzdHMuY29va2ll\ncwpSZXF1ZXN0c0Nvb2tpZUphcgpxMCmBcTF9cTIoWAcAAABfcG9saWN5cTNjaHR0cC5jb29raWVq\nYXIKRGVmYXVsdENvb2tpZVBvbGljeQpxNCmBcTV9cTYoWAgAAABuZXRzY2FwZXE3iFgHAAAAcmZj\nMjk2NXE4iVgTAAAAcmZjMjEwOV9hc19uZXRzY2FwZXE5TlgMAAAAaGlkZV9jb29raWUycTqJWA0A\nAABzdHJpY3RfZG9tYWlucTuJWBsAAABzdHJpY3RfcmZjMjk2NV91bnZlcmlmaWFibGVxPIhYFgAA\nAHN0cmljdF9uc191bnZlcmlmaWFibGVxPYlYEAAAAHN0cmljdF9uc19kb21haW5xPksAWBwAAABz\ndHJpY3RfbnNfc2V0X2luaXRpYWxfZG9sbGFycT+JWBIAAABzdHJpY3RfbnNfc2V0X3BhdGhxQIlY\nEAAAAF9ibG9ja2VkX2RvbWFpbnNxQSlYEAAAAF9hbGxvd2VkX2RvbWFpbnNxQk5YBAAAAF9ub3dx\nQ0p77CJddWJoL31xRGhDSnvsIl11YlgEAAAAYm9keXFFQzl7Impzb25ycGMiOiAiMi4wIiwgIm1l\ndGhvZCI6ICJpY3hfZ2V0TGFzdEJsb2NrIiwgImlkIjogMX1xRlgFAAAAaG9va3NxR31xSGgIXXFJ\nc1gOAAAAX2JvZHlfcG9zaXRpb25xSk51YnViLg==\n"}
{"number": 2, "type": "dict", "contents": {"version": "0.1a", "prev_block_hash": "fd56f96d3ecbb6ce1a1f8389b25720aaf0ec4bbfe4ed94f84a180062af3e1939", "merkle_tree_root_hash": "3f47d0c0dbfb595f0cd579079e9902bc7684de986c077bfe7010c9e45e826fa8", "time_stamp": 1562569821740399, "confirmed_transaction_list": [{"version": "0x3", "from": "hx226e6e4340136836b36977bd76ca83746b8b071c", "to": "cxb7ef03fea5fa9b2fe1f00f548d6da7ff2ddfebd5", "stepLimit": "0x989680", "timestamp": "0x58d26231eace3", "nid": "0x1", "nonce": "0x64", "dataType": "call", "data": {"method": "transaction_RT", "params": {"_date": "20190708", "_time": "0710", "_div": "GOOGLE", "_value": "[\"Mickey's Toontown\", \"Bella Thorne\", \"Concacaf Gold Cup\", \"Concacaf Gold Cup\", \"Earthquake\"]"}}, "signature": "D/jST80Laod+JDZPs086m8uCWAhcu3aqGCemIOqF1edGOfyg0LmcNcur94wyCFo5FRRwQDgAbsB+aIzyQmfgxgE=", "txHash": "0x3f47d0c0dbfb595f0cd579079e9902bc7684de986c077bfe7010c9e45e826fa8"}], "block_hash": "205c3e0fff2f4ac53c18b293d814ee728859a733f2bcd4829f945538e37de717", "height": 5727019, "peer_id": "hxba25b9ec30db3e0d5f3b914b5af46119bbdf7626", "signature": "ee48zbiS/RRRDlHEubWmoQeQouOdnDFglDxKS9TNCVcsTr1xvvqi7wIwheOiQBY8XvW/9i4ZEXsbTk86C/84GwA=", "next_leader": "hxba25b9ec30db3e0d5f3b914b5af46119bbdf7626"}}
{"number": 3, "type": "dict", "contents": {"version": "0.1a", "prev_block_hash": "fd56f96d3ecbb6ce1a1f8389b25720aaf0ec4bbfe4ed94f84a180062af3e1939", "merkle_tree_root_hash": "3f47d0c0dbfb595f0cd579079e9902bc7684de986c077bfe7010c9e45e826fa8", "time_stamp": 1562569821740399, "confirmed_transaction_list": [{"version": "0x3", "from": "hx226e6e4340136836b36977bd76ca83746b8b071c", "to": "cxb7ef03fea5fa9b2fe1f00f548d6da7ff2ddfebd5", "stepLimit": "0x989680", "timestamp": "0x58d26231eace3", "nid": "0x1", "nonce": "0x64", "dataType": "call", "data": {"method": "transaction_RT", "params": {"_date": "20190708", "_time": "0710", "_div": "GOOGLE", "_value": "[\"Mickey's Toontown\", \"Bella Thorne\", \"Concacaf Gold Cup\", \"Concacaf Gold Cup\", \"Earthquake\"]"}}, "signature": "D/jST80Laod+JDZPs086m8uCWAhcu3aqGCemIOqF1edGOfyg0LmcNcur94wyCFo5FRRwQDgAbsB+aIzyQmfgxgE=", "txHash": "0x3f47d0c0dbfb595f0cd579079e9902bc7684de986c077bfe7010c9e45e826fa8"}], "block_hash": "205c3e0fff2f4ac53c18b293d814ee728859a733f2bcd4829f945538e37de717", "height": 5727019, "peer_id": "hxba25b9ec30db3e0d5f3b914b5af46119bbdf7626", "signature": "ee48zbiS/RRRDlHEubWmoQeQouOdnDFglDxKS9TNCVcsTr1xvvqi7wIwheOiQBY8XvW/9i4ZEXsbTk86C/84GwA=", "next_leader": "hxba25b9ec30db3e0d5f3b914b5af46119bbdf7626"}}
"""


if __name__ == "__main__":
    test_event_system()
