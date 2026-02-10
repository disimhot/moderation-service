import logging
from .core import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def seed_db() -> None:
    """Initialize and seed the database."""
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized successfully.")


if __name__ == "__main__":
    seed_db()
