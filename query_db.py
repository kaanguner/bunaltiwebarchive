import os
import sys
import psycopg2
from dotenv import load_dotenv
from tabulate import tabulate  # pip install tabulate

# Load environment variables
load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    print("Error: DATABASE_URL environment variable not set.")
    print("Please create a .env file with DATABASE_URL='postgresql://user:password@host:port/database'")
    sys.exit(1)

def connect_db():
    """Establishes a PostgreSQL database connection."""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        print("PostgreSQL connection successful.")
        return conn
    except psycopg2.OperationalError as e:
        print(f"Database Connection Error: {e}")
        print("Please check your DATABASE_URL, network connection, and DB server status.")
        return None
    except Exception as e:
        print(f"Database connection failed with an unexpected error: {e}")
        return None

def execute_query(conn, query, params=None):
    """Executes a query and returns the results."""
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute(query, params or ())
        
        if query.strip().upper().startswith(('SELECT', 'SHOW', 'DESCRIBE', 'EXPLAIN')):
            # Fetch column names
            column_names = [desc[0] for desc in cursor.description]
            # Fetch all results
            results = cursor.fetchall()
            return True, column_names, results
        else:
            # For non-SELECT queries (INSERT, UPDATE, DELETE, etc.)
            affected_rows = cursor.rowcount
            conn.commit()
            return True, None, f"Query executed successfully. Rows affected: {affected_rows}"
    except Exception as e:
        conn.rollback()
        return False, None, f"Error executing query: {e}"
    finally:
        if cursor:
            cursor.close()

def display_results(success, columns, results):
    """Displays query results in a readable format."""
    if not success:
        print(results)  # Display error message
        return
    
    if columns:  # SELECT query with results
        if not results:
            print("Query returned no results.")
            return
        
        print(tabulate(results, headers=columns, tablefmt="psql"))
        print(f"\nTotal rows: {len(results)}")
    else:  # Non-SELECT query
        print(results)

def main():
    conn = connect_db()
    if not conn:
        sys.exit(1)
    
    try:
        while True:
            print("\n" + "="*50)
            print("Enter your SQL query (or 'exit' to quit, 'clear' to clear screen):")
            print("="*50)
            
            # Collect multi-line query
            lines = []
            while True:
                line = input("> " if not lines else "... ")
                if line.strip().lower() == 'exit':
                    print("Exiting...")
                    return
                elif line.strip().lower() == 'clear':
                    os.system('cls' if os.name == 'nt' else 'clear')
                    break
                elif line.strip().endswith(';'):
                    lines.append(line)
                    break
                elif line.strip():
                    lines.append(line)
                else:
                    # Empty line - if we have content, end query
                    if lines:
                        break
            
            if not lines:
                continue
                
            query = '\n'.join(lines)
            
            # Execute and display results
            print("\nExecuting query...\n")
            success, columns, results = execute_query(conn, query)
            display_results(success, columns, results)
            
    except KeyboardInterrupt:
        print("\nScript terminated by user.")
    finally:
        if conn:
            conn.close()
            print("Database connection closed.")

if __name__ == "__main__":
    main()