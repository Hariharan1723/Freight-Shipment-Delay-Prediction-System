import mysql.connector
from mysql.connector import Error
import logging

logger = logging.getLogger(__name__)


def get_connection():
    """
    Returns a MySQL connection.
    Raises an exception if connection fails.
    """
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="test",
            database="logistics_analytics_2",
            connection_timeout=10
        )
        if conn.is_connected():
            logger.info("MySQL connection established.")
            return conn
    except Error as e:
        logger.error(f"MySQL connection failed: {e}")
        raise