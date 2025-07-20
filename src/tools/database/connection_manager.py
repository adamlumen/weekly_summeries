"""
Snowflake Connection Manager for persistent connections across tool executions.
Manages SSO authentication and connection reuse to avoid repeated login prompts.
"""

import logging
import threading
from typing import Optional, Dict, Any
import snowflake.connector as sf
import pandas as pd
from datetime import datetime, timedelta

from .utilities import get_snowflake_settings

logger = logging.getLogger(__name__)

class SnowflakeConnectionManager:
    """
    Singleton class to manage persistent Snowflake connections.
    Prevents repeated SSO authentication by reusing connections.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(SnowflakeConnectionManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.connection = None
            self.connection_time = None
            self.connection_timeout = timedelta(hours=1)  # Reuse connection for 1 hour
            self.sf_settings = None
            self.initialized = True
            logger.info("SnowflakeConnectionManager initialized")
    
    def get_connection(self):
        """
        Get an active Snowflake connection, reusing existing one if valid.
        
        Returns:
            snowflake.connector.connection: Active Snowflake connection
        """
        with self._lock:
            # Check if we have a valid existing connection
            if self._is_connection_valid():
                logger.debug("Reusing existing Snowflake connection")
                return self.connection
            
            # Create new connection
            logger.info("Creating new Snowflake connection")
            return self._create_new_connection()
    
    def _is_connection_valid(self) -> bool:
        """Check if current connection is still valid and not expired."""
        if self.connection is None or self.connection_time is None:
            return False
        
        # Check if connection has expired
        if datetime.now() - self.connection_time > self.connection_timeout:
            logger.debug("Snowflake connection expired")
            self._close_connection()
            return False
        
        # Test if connection is still active
        try:
            # Simple test query to check connection
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT CURRENT_TIMESTAMP()")
                cursor.fetchone()
            logger.debug("Snowflake connection is still valid")
            return True
        except Exception as e:
            logger.warning(f"Snowflake connection test failed: {e}")
            self._close_connection()
            return False
    
    def _create_new_connection(self):
        """Create a new Snowflake connection."""
        try:
            # Get fresh settings
            self.sf_settings = get_snowflake_settings()
            
            # Close any existing connection
            self._close_connection()
            
            # Create new connection
            self.connection = sf.connect(**self.sf_settings)
            self.connection_time = datetime.now()
            
            logger.info("New Snowflake connection established")
            return self.connection
            
        except Exception as e:
            logger.error(f"Failed to create Snowflake connection: {e}")
            self.connection = None
            self.connection_time = None
            raise
    
    def _close_connection(self):
        """Close the current connection."""
        if self.connection:
            try:
                self.connection.close()
                logger.debug("Snowflake connection closed")
            except Exception as e:
                logger.warning(f"Error closing Snowflake connection: {e}")
            finally:
                self.connection = None
                self.connection_time = None
    
    def execute_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """
        Execute a SQL query using the managed connection.
        
        Args:
            query: SQL query to execute
            parameters: Optional parameters for parameterized queries
            
        Returns:
            pd.DataFrame: Query results
        """
        connection = self.get_connection()
        
        try:
            # Replace parameters if provided
            if parameters:
                query = query.format(**parameters)
            
            # Execute query
            df = pd.read_sql(query, connection)
            logger.debug(f"Query executed successfully, returned {len(df)} rows")
            return df
            
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            # If query fails, try to reconnect once
            if "Invalid connection" in str(e) or "Connection is closed" in str(e):
                logger.info("Connection seems closed, attempting to reconnect...")
                self._close_connection()
                connection = self.get_connection()
                df = pd.read_sql(query, connection)
                logger.debug(f"Query executed successfully after reconnect, returned {len(df)} rows")
                return df
            else:
                raise
    
    def test_connection(self) -> bool:
        """
        Test if we can establish a connection to Snowflake.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            connection = self.get_connection()
            with connection.cursor() as cursor:
                cursor.execute("SELECT CURRENT_DATE()")
                result = cursor.fetchone()
                logger.info(f"Snowflake connection test successful. Current date: {result[0]}")
                return True
        except Exception as e:
            logger.error(f"Snowflake connection test failed: {e}")
            return False
    
    def cleanup(self):
        """Cleanup resources when shutting down."""
        logger.info("Cleaning up Snowflake connection manager")
        self._close_connection()

# Global instance
snowflake_manager = SnowflakeConnectionManager()
