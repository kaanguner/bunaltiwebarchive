# remove_replacement_char_db.py
import os
import sys
import psycopg2
from dotenv import load_dotenv

# --- Configuration ---
load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')
TARGET_CHAR = '�' # The Unicode Replacement Character U+FFFD

# --- Main Execution ---
if __name__ == "__main__":
    print("Starting final cleanup: Removing Unicode Replacement Character...")
    print("="*60)
    print(f"!!! WARNING: This script will PERMANENTLY REMOVE all occurrences !!!")
    print(f"!!! of the character '{TARGET_CHAR}' from the 'comments.content' column. !!!")
    print("!!! Ensure you have a database backup before proceeding. !!!")
    print("="*60)

    confirm = input(f"Type 'REMOVE {TARGET_CHAR}' to confirm you wish to proceed: ")
    # Require specific confirmation to prevent accidental execution
    if confirm != f'REMOVE {TARGET_CHAR}':
        print("Confirmation incorrect. Operation cancelled.")
        sys.exit()

    conn = None
    cursor = None
    try:
        print(f"\nConnecting to database...")
        if not DATABASE_URL:
            raise ValueError("DATABASE_URL environment variable not set.")

        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        print("Database connection successful.")

        # --- Perform the UPDATE ---
        sql_update = f"UPDATE comments SET content = REPLACE(content, %s, '') WHERE content LIKE %s;"
        like_pattern = f'%{TARGET_CHAR}%'

        print(f"Executing UPDATE to remove '{TARGET_CHAR}' from comments.content...")
        # Pass TARGET_CHAR and the like pattern as parameters to avoid SQL injection issues
        cursor.execute(sql_update, (TARGET_CHAR, like_pattern))
        row_count = cursor.rowcount # Get the number of rows affected
        conn.commit() # Commit the changes

        print(f"\n--- UPDATE complete. ---")
        print(f"--- Removed '{TARGET_CHAR}' from {row_count} rows in comments.content. ---")

    except ValueError as e:
        print(f"!!! Configuration Error: {e}")
    except psycopg2.Error as e: # Catch specific psycopg2 errors
        print(f"!!! Database Error occurred: {e}")
        if conn:
            conn.rollback() # Rollback on error
        print("Transaction rolled back due to error.")
    except Exception as e:
        print(f"!!! An unexpected error occurred: {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
            print("\nDatabase connection closed.")