import time

from beams.service.remote_calls.generic_message_pb2 import MessageType
from beams.service.rpc_client import RPCClient
from beams.service.rpc_handler import RPCHandler


class TestRPC:
    def test_simple(self):
        p = RPCHandler()
        p.start_work()

        time.sleep(1)

        c = RPCClient()
        c.run(command="get_heartbeat")

        p.stop_work()

        time_sec = time.time()

        assert c.response.mess_t == MessageType.MESSAGE_TYPE_HEARTBEAT
        assert (c.response.reply_timestamp.ToSeconds() - time_sec) < 1
        time.sleep(.1)
