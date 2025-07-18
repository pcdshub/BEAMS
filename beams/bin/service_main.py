import logging
import time

from beams.logging import setup_logging
from beams.service.rpc_handler import BeamsService

logger = logging.getLogger(__name__)


def main(*args, **kwargs):
    service = BeamsService()
    service.start_work()

    while (input("press q+<enter> to kill") != 'q'):
        time.sleep(1)
    service.join_all_trees()
    service.stop_work()


if __name__ == "__main__":
    setup_logging(logging.DEBUG)
    main()
