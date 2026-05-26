from __future__ import annotations

import logging
import os
import sys


def setup_logging() -> None:
    level_name = os.environ.get("ESCSMM_LOG", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stderr,
    )
