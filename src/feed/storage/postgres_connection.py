# Dummy module to satisfy ModuleNotFoundError in old system components
# The project uses MySQL for task persistence, so this module is not used.
import logging
logger = logging.getLogger(__name__)

def get_postgres_connection():
    logger.warning("Attempted to call get_postgres_connection. Using MySQL for persistence instead.")
    raise NotImplementedError("PostgreSQL connection is not implemented in this configuration.")