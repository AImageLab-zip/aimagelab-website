#!/usr/bin/env python3
"""
Wait for database to be ready before starting Django application.
"""
import os
import sys
import time
import MySQLdb
from MySQLdb import OperationalError

def wait_for_db():
    """Wait for MySQL database to be ready."""
    db_host = os.environ.get('DB_HOST', 'mysql-db')
    db_name = os.environ.get('DB_NAME', 'aimagelab_db')
    db_user = os.environ.get('DB_USER', 'aimagelab_user')
    db_password = os.environ.get('DB_PASSWORD', 'aimagelab_pass123')
    db_port = int(os.environ.get('DB_PORT', '3306'))
    
    max_retries = 30
    retry_interval = 2
    
    print(f"Waiting for database at {db_host}:{db_port}...")
    
    for attempt in range(max_retries):
        try:
            connection = MySQLdb.connect(
                host=db_host,
                user=db_user,
                passwd=db_password,
                db=db_name,
                port=db_port
            )
            connection.close()
            print("✓ Database is ready!")
            return True
        except OperationalError as e:
            if attempt < max_retries - 1:
                print(f"Database not ready (attempt {attempt + 1}/{max_retries}), waiting...")
                time.sleep(retry_interval)
            else:
                print(f"✗ Failed to connect to database after {max_retries} attempts")
                print(f"Error: {e}")
                sys.exit(1)
    
    return False

if __name__ == '__main__':
    wait_for_db()
