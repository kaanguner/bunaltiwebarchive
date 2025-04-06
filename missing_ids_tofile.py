import os
import sys
import psycopg2
import logging
from dotenv import load_dotenv
from tabulate import tabulate
import re
import json
import html
from bs4 import BeautifulSoup
import argparse
from datetime import datetime

# --- Setup Logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("re_extract_comments.log"),
        logging.StreamHandler()
    ]
)

# --- Load Env Vars and DB Connect (Keep as is) ---
load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')
# ... (rest of DB setup and connect_db, execute_query, display_results, normalize_query) ...
# --- Load Env Vars and DB Connect ---
if not DATABASE_URL:
    print("Error: DATABASE_URL environment variable not set.")
    print("Please create a .env file with DATABASE_URL='postgresql://user:password@host:port/database'")
    sys.exit(1)

def connect_db():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        print("PostgreSQL connection successful.")
        return conn
    except psycopg2.OperationalError as e:
        print(f"Database Connection Error: {e}"); return None
    except Exception as e:
        print(f"Database connection failed: {e}"); return None

def execute_query(conn, query, params=None):
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute(query, params or ())
        is_select = query.strip().upper().startswith(('SELECT', 'SHOW', 'DESCRIBE', 'EXPLAIN', 'WITH'))
        if is_select and cursor.description:
            column_names = [desc[0] for desc in cursor.description]; results = cursor.fetchall()
            return True, column_names, results
        elif is_select: return True, [], []
        else:
            affected_rows = cursor.rowcount; conn.commit()
            return True, None, f"Query executed successfully. Rows affected: {affected_rows}"
    except Exception as e: conn.rollback(); return False, None, f"Error executing query: {e}"
    finally:
        if cursor: cursor.close()

def display_results(success, columns, results):
    if not success: print(f"\nError: {results}"); return
    if isinstance(results, str): print(f"\n{results}"); return
    if columns is None: print("\nQuery executed, but no column info (non-SELECT?)."); return
    if not results: print("\nQuery returned no results."); return
    try:
        print("\n" + tabulate(results, headers=columns, tablefmt="psql")); print(f"\nTotal rows: {len(results)}")
    except Exception as e:
        print(f"\nError formatting results: {e}"); print("Raw results:");
        for row in results[:10]: print(row)
        if len(results) > 10: print("...")

def normalize_query(query_string):
    return ' '.join(query_string.lower().split())


# --- CORRECTED save_results_to_file ---
def save_results_to_file(filename, results):
    """Saves the first column of query results to a text file."""
    full_path = os.path.abspath(filename) # Get absolute path for clarity

    # --- ADDED DEBUG PRINTS ---
    current_dir = os.getcwd()
    logging.info(f"Current working directory for saving: {current_dir}")
    logging.info(f"Attempting to save results to absolute path: {full_path}")
    print(f"DEBUG: Saving to absolute path: {full_path}") # Crucial debug output
    # --- END OF ADDED DEBUG PRINTS ---

    try:
        count = 0
        if not isinstance(results, list):
            logging.error(f"Cannot save results: Expected a list, got {type(results)}")
            print(f"\nError: Internal error preparing data for saving.")
            return False
        if not results:
            logging.warning("Cannot save results: The result list is empty.")
            print("\nWarning: Query returned results, but data list was empty before saving.")
            return False # Treat as non-success if nothing to write

        with open(full_path, 'w', encoding='utf-8') as f:
            for row in results:
                if row and len(row) > 0:
                    try:
                        f.write(str(row[0]) + '\n')
                        count += 1
                    except IndexError: logging.warning(f"Skipping row with unexpected format (IndexError): {row}")
                    except Exception as write_err: logging.error(f"Error writing row '{row}' to file: {write_err}"); # Maybe continue?
                else:
                    logging.warning(f"Skipping empty or invalid row: {row}")

        # Verify file creation and content
        if os.path.exists(full_path) and os.path.getsize(full_path) > 0:
             logging.info(f"Successfully saved {count} IDs to {full_path}")
             print(f"\nSuccessfully saved {count} IDs to {filename}")
             return True
        elif count > 0:
             logging.error(f"Wrote {count} rows but file '{full_path}' seems empty/missing after write.")
             print(f"\nError: Wrote data but could not confirm file '{filename}'. Check permissions/disk space.")
             return False
        else:
             logging.warning(f"No valid rows were written to file '{full_path}'.")
             print(f"\nWarning: No valid data found to save to '{filename}'.")
             return False # No data written = not a success

    except PermissionError:
        logging.error(f"Permission denied when trying to write to {full_path}")
        print(f"\nError: Permission denied writing to file '{filename}'. Check directory permissions.")
        return False
    except OSError as e:
        logging.error(f"OS error saving results to file {full_path}: {e}")
        print(f"\nError saving results to file '{filename}': {e}")
        return False
    except Exception as e:
        logging.error(f"Unexpected error saving results to file {full_path}: {e}", exc_info=True)
        print(f"\nUnexpected error saving results to file '{filename}': {e}")
        return False

# --- main function with export logic (ensure it calls the corrected save function) ---
def main():
    conn = connect_db()
    if not conn: sys.exit(1)
    target_query = "select id from posts where id not in ( select distinct post_id from comments );"
    target_query_normalized = normalize_query(target_query)
    output_filename = "missing_comment_post_ids.txt"
    try:
        while True:
            print("\n" + "="*50); print("Enter SQL query (end with ';' or empty line, 'exit', 'clear', 'export_missing' for specific query):"); print("="*50)
            lines = []; query_to_run = None
            while True:
                line = input("> " if not lines else "... ")
                command = line.strip().lower()
                if command == 'exit': print("Exiting..."); return
                elif command == 'clear': os.system('cls' if os.name == 'nt' else 'clear'); lines = []; print("\n" + "="*50); print("Enter SQL query..."); print("="*50); continue
                elif command == 'export_missing': query_to_run = target_query; print(f"... executing specific query to export missing comment IDs..."); break
                elif line.strip().endswith(';'): lines.append(line); query_to_run = '\n'.join(lines).strip(); break
                elif line.strip(): lines.append(line)
                elif lines: query_to_run = '\n'.join(lines).strip(); break
            if not query_to_run: continue # Handle empty input after clear/initial prompt
            normalized_user_query = normalize_query(query_to_run)

            # --- Special Handling OR Normal Handling ---
            if normalized_user_query == target_query_normalized:
                print(f"\nExecuting specific query to save results to '{output_filename}'...\n")
                success, columns, results = execute_query(conn, query_to_run) # Use the query
                if success:
                    if isinstance(results, list):
                        if results: save_results_to_file(output_filename, results) # Call save function
                        else: print("Query returned no results (no missing IDs found). File not created.")
                    else: print(f"Query executed with message, but expected rows: {results}")
                else: print(f"Query failed: {results}")
            else: # Normal query execution
                print("\nExecuting query...\n"); success, columns, results = execute_query(conn, query_to_run); display_results(success, columns, results)

    except KeyboardInterrupt: print("\nScript terminated by user.")
    finally:
        if conn: conn.close(); print("\nDatabase connection closed.")

if __name__ == "__main__":
    # No argparse needed for this specific script if paths are hardcoded or used via .env
    main()