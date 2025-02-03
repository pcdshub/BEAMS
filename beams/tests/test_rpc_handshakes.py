import time
from types import SimpleNamespace

from beams.service.rpc_handler import RPCHandler
from beams.service.rpc_client import RPCClient

from beams.service.remote_calls.generic_message_pb2 import MessageType


class TestRPC:
    def test_simple(self):
        p = RPCHandler()
        p.start_work()

        time.sleep(1)

        args = SimpleNamespace(hbeat=True)
        c = RPCClient(args)
        c.run()

        p.stop_work()

        time_sec = time.time()

        assert c.response.mess_t == MessageType.MESSAGE_TYPE_HEARTBEAT
        assert (c.response.reply_timestamp.ToSeconds() - time_sec) < 1
        time.sleep(.1)
