import logging

from apischema.validation.errors import ValidationError

from beams.tree_config import get_tree_from_path

logger = logging.getLogger(__name__)


def main(filepath: str):
    try:
        get_tree_from_path(filepath)
        logger.info("File validation successful! File is well-formed.")
        return 0
    except ValidationError as exc:
        logger.error(f"Schema validation error for {filepath}: {exc}")
        logger.debug("", exc_info=True)
        return 1
    except Exception as exc:
        logger.error(f"Error when processing {filepath}: {exc}")
        logger.debug("", exc_info=True)
        return 1
