"""
Database Connection Manager for OpenCart Integration
Provides secure database connections with pooling and error handling
"""

import mysql.connector
from mysql.connector import pooling
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from contextlib import contextmanager
import os
from datetime import datetime

@dataclass
class DatabaseConfig:
    """Configuration for database connection"""
    host: str
    username: str
    password: str
    database: str
    port: int = 3306
    prefix: str = 'oc_'

class DatabaseConnectionManager:
    """Manages database connections with pooling for OpenCart"""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.pool = None
        self._create_connection_pool()
        
    def _create_connection_pool(self):
        """Create database connection pool"""
        try:
            pool_config = {
                'pool_name': 'audico_pool',
                'pool_size': 10,
                'pool_reset_session': True,
                'host': self.config.host,
                'port': self.config.port,
                'database': self.config.database,
                'user': self.config.username,
                'password': self.config.password,
                'charset': 'utf8mb4',
                'collation': 'utf8mb4_unicode_ci',
                'autocommit': True
            }
            
            self.pool = mysql.connector.pooling.MySQLConnectionPool(**pool_config)
            logging.info("Database connection pool created successfully")
            
        except Exception as e:
            logging.error(f"Failed to create connection pool: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        connection = None
        try:
            connection = self.pool.get_connection()
            yield connection
        except Exception as e:
            if connection:
                connection.rollback()
            logging.error(f"Database operation failed: {e}")
            raise
        finally:
            if connection:
                connection.close()
    
    def execute_query(self, query: str, params: tuple = None) -> List[Dict]:
        """Execute SELECT query and return results"""
        with self.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, params)
            results = cursor.fetchall()
            cursor.close()
            return results
    
    def execute_insert(self, query: str, params: tuple = None) -> int:
        """Execute INSERT query and return last insert ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            last_id = cursor.lastrowid
            conn.commit()
            cursor.close()
            return last_id
    
    def execute_update(self, query: str, params: tuple = None) -> int:
        """Execute UPDATE query and return affected rows"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            affected_rows = cursor.rowcount
            conn.commit()
            cursor.close()
            return affected_rows
    
    def get_table_name(self, table: str) -> str:
        """Get full table name with prefix"""
        return f"{self.config.prefix}{table}"
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                cursor.close()
                return True
        except Exception as e:
            logging.error(f"Connection test failed: {e}")
            return False

# Global database manager instance
db_manager = None

def initialize_database(host: str, username: str, password: str, database: str, port: int = 3306, prefix: str = 'oc_'):
    """Initialize global database manager"""
    global db_manager
    config = DatabaseConfig(
        host=host,
        username=username,
        password=password,
        database=database,
        port=port,
        prefix=prefix
    )
    db_manager = DatabaseConnectionManager(config)
    return db_manager

def get_database_manager() -> DatabaseConnectionManager:
    """Get global database manager instance"""
    if db_manager is None:
        raise RuntimeError("Database not initialized. Call initialize_database() first.")
    return db_manager
