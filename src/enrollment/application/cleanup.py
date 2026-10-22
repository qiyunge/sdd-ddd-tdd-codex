"""Cleanup preserves the primary exception and records secondary failures."""

import logging
import sys

from .ports import Closable


def close_preserving_failure(resource: Closable) -> None:
    primary = sys.exception()
    try:
        resource.close()
    except Exception:
        if primary is None:
            raise
        logging.getLogger(__name__).exception(
            "Cleanup failed while preserving primary error"
        )
