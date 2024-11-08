import logging

from apischema.validation.errors import ValidationError

from beams.tree_config import get_tree_from_path

logger = logging.getLogger(__name__)


def main(filepath: str) -> int:
    """
    Try to deserialize the tree, and return a nonzero return code if we can't.

    For the failure cases, give the exception text.
    If log level is DEBUG or lower, show the full traceback.
    """
    try:
        get_tree_from_path(filepath)
        logger.info(f"Schema validation successful! {filepath} is well-formed.")
        return 0
    except ValidationError as exc:
        logger.error(f"Schema validation error for {filepath}: {exc}")
        logger.debug("", exc_info=True)
        return 1
    except Exception as exc:
        logger.error(f"Error when processing {filepath}: {exc}")
        logger.debug("", exc_info=True)
        return 2
