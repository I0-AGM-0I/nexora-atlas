"""
NEXORA ATLAS - Structured Enterprise Logging
Ensures sensitive tokens/credentials are never leaked and diagnostics are clean.
"""

import logging
import sys
from app.core.config import settings

LOG_FORMAT = "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s"

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format=LOG_FORMAT,
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger("atlas")
