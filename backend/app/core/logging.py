"""
logging.py — Application-Wide Logging Configuration

Purpose:
- Configure a standardized logging format for the entire backend.
- Ensure consistency across API requests, ingestion workflows, and modeling runs.
- Provide human-readable logs during development and structured logs for production.

MVP Goals:
- Simple console logging at INFO level.
- Uniform formatting: timestamp | level | module | message
- No external log aggregation (yet).

Future Upgrades:
- Add JSON logging mode for ingestion job traceability.
- Add structured pipeline logging for multi-step workflows.
- Integrate with hosted log collection (e.g., Loki, Datadog, CloudWatch).
"""

import logging

# -----------------------------------------------------------------------------
# Log Format
# -----------------------------------------------------------------------------

LOG_FORMAT = (
    "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

# -----------------------------------------------------------------------------
# Root Logger Initialization
# -----------------------------------------------------------------------------

def configure_logging(level: str = "INFO") -> None:
    """
    Configure root logging settings.

    Parameters:
        level (str): "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"

    Behavior:
    - Sets logging format globally.
    - Ensures logs stream to stdout (FastAPI / Uvicorn picks this up).
    - Should be called ONCE, typically in `main.py` at app startup.

    Example Call:
        configure_logging("DEBUG")
    """

    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format=LOG_FORMAT
    )

    # Log that logging has been configured (helps confirm initialization in debug)
    logging.getLogger(__name__).info("Logging initialized with level %s", level)

# -----------------------------------------------------------------------------
# Logger Access Helper
# -----------------------------------------------------------------------------

def get_logger(name: str) -> logging.Logger:
    """
    Return a logger instance to be used in any module.

    Best Practice:
    In any module:
        from app.core.logging import get_logger
        logger = get_logger(__name__)
        logger.info("something happened")

    This avoids different modules manually configuring their own loggers.
    """
    return logging.getLogger(name)
