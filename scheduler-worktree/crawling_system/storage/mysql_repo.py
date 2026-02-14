import os
from typing import List, Tuple, Dict, Any, Optional
import mysql.connector
from mysql.connector import connection
from tenacity import retry, stop_after_attempt, wait_fixed, RetryError
import time

class MySQLRepository:
    """
    Manages connections and transactions for the Control Plane (MySQL).
    Handles targets, subscriptions, and crawl job logging.
    """
    def __init__(self,
                 host: str = "crawler_mysql_control",
                 user: str = "root",
                 password: str = "secret",
                 database: str = "crawler_control"):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self._conn: Optional[connection.MySQLConnection] = None

    @retry(stop=stop_after_attempt(5), wait=wait_fixed(2))
    def _get_connection(self) -> connection.MySQLConnection:
        """Establishes a connection to the MySQL database."""
        if self._conn is None or not self._conn.is_connected():
            print(f"Connecting to MySQL at {self.host}...")
            self._conn = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
        return self._conn

    def close(self):
        """Closes the database connection."""
        if self._conn and self._conn.is_connected():
            self._conn.close()
        self._conn = None

    def get_active_targets(self) -> List[Dict[str, Any]]:
        """
        Retrieves a list of all active targets that need crawling.
        """
        query = """
        SELECT id, target_type, value, last_crawled_at 
        FROM targets 
        WHERE is_active = TRUE
        """
        conn = self._get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query)
        targets = cursor.fetchall()
        cursor.close()
        return targets

    def add_new_target(self, target_type: str, value: str, description: str, user_id: int = 1) -> Optional[int]:
        """
        Inserts a new target and subscribes a user to it.
        
        Returns:
            The ID of the newly created target or None on failure/if already exists.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # 1. Insert/Find Target
            query_target = """
            INSERT INTO targets (target_type, value, description)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE id=LAST_INSERT_ID(id)
            """
            cursor.execute(query_target, (target_type, value, description))
            target_id = cursor.lastrowid or self._get_existing_target_id(target_type, value)

            if not target_id:
                raise Exception("Failed to get target ID.")
            
            # 2. Subscribe User
            query_sub = """
            INSERT IGNORE INTO user_subscriptions (user_id, target_id)
            VALUES (%s, %s)
            """
            cursor.execute(query_sub, (user_id, target_id))
            conn.commit()
            cursor.close()
            return target_id
            
        except Exception as e:
            print(f"Error adding new target/subscription: {e}")
            return None

    def _get_existing_target_id(self, target_type: str, value: str) -> Optional[int]:
        """Helper to fetch ID of an existing target."""
        query = "SELECT id FROM targets WHERE target_type = %s AND value = %s"
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(query, (target_type, value))
        result = cursor.fetchone()
        cursor.close()
        return result[0] if result else None

    def log_job_start(self, target_id: int) -> int:
        """
        Logs a new job in the crawl_jobs table with status 'PROCESSING'.
        
        Returns:
            The ID of the newly created crawl job.
        """
        query = """
        INSERT INTO crawl_jobs (target_id, status, started_at)
        VALUES (%s, %s, %s)
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        now = datetime.datetime.now()
        cursor.execute(query, (target_id, "PROCESSING", now))
        
        job_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        
        # Update last_crawled_at on the target immediately to prevent duplicates
        self._update_target_last_crawled(target_id)
        
        return job_id

    def log_job_complete(self, job_id: int, items_collected: int, minio_path: str, status: str = "COMPLETED", error_message: Optional[str] = None):
        """
        Updates the status of a crawl job.
        """
        query = """
        UPDATE crawl_jobs
        SET status = %s, items_collected = %s, minio_path = %s, completed_at = %s, error_message = %s
        WHERE id = %s
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        now = datetime.datetime.now()
        
        cursor.execute(query, (status, items_collected, minio_path, now, error_message, job_id))
        conn.commit()
        cursor.close()

    def _update_target_last_crawled(self, target_id: int):
        """Updates the last_crawled_at timestamp on the targets table."""
        query = """
        UPDATE targets
        SET last_crawled_at = %s
        WHERE id = %s
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        now = datetime.datetime.now()
        cursor.execute(query, (now, target_id))
        conn.commit()
        cursor.close()

# Temporary import of datetime until the main loop uses this class
import datetime
