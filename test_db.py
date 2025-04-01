import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL from environment
database_url = os.getenv('DATABASE_URL')

# Test connection
try:
    conn = psycopg2.connect(database_url)
    print("Connection successful!")
    
    # Create a cursor
    cursor = conn.cursor()
    
    # Execute a simple query
    cursor.execute("SELECT version();")
    db_version = cursor.fetchone()
    print(f"PostgreSQL version: {db_version[0]}")
    
    # Close connection
    cursor.close()
    conn.close()
except Exception as e:
    print(f"Error connecting to the database: {e}")