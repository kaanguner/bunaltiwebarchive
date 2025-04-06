import re
import os
import sys
import psycopg2 # Ensure this is installed: pip install psycopg2-binary
from dotenv import load_dotenv
import time

# --- Load Environment Variables ---
load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    print("Error: DATABASE_URL environment variable not set.")
    print("Please create a .env file with DATABASE_URL='postgresql://user:password@host:port/database'")
    sys.exit(1)

# --- Database Schema Configuration (Adjust if necessary) ---
COMMENTS_TABLE = 'comments'
COMMENT_ID_COLUMN = 'id'
COMMENT_AUTHOR_COLUMN = 'author'
COMMENT_CONTENT_COLUMN = 'content'

# --- The Specific Garbled Character to Find ---
GARBLED_CHAR = 'Ã' # Unicode U+00C3

# --- Word Replacement Map (From your fixing script) ---
# Keys use ACTUAL GARBLED characters. Values are correct lowercase Turkish.
WORD_REPLACEMENT_MAP = {
    'gerÃekten': 'gerçekten', 'Ãok': 'çok', 'mÃkemmel': 'mükemmel', 'sÃper': 'süper',
    'tÃr': 'tür', 'bötÃn': 'bütün', 'gözel': 'güzel', 'mözik': 'müzik',
    'düşÃnerek': 'düşünerek', 'yözden': 'yüzden', 'Ãocuk': 'çocuk', 'Ãift': 'çift',
    'sÃrekli': 'sürekli', 'Ãstad': 'üstad', 'sÃven': 'söven', 'gÃre': 'göre',
    'kÃtÃ': 'kötü', 'göldürsÃn': 'güldürsün', 'Ãalışan': 'çalışan',
    'Ãekmeye': 'çekmeye', 'Ãnereceğiniz': 'önereceğiniz', 'Ãnerir': 'önerir',
    'Ãdöl': 'ödül', 'professyÃnel': 'profesyonel', 'yÃceltilecek': 'yüceltilecek',
    'görÃrsÃnöz': 'görürsünüz', 'albümÃ': 'albümü', 'albÃm': 'albüm',
    'parÃalar': 'parçalar', 'teşekkÃ rler': 'teşekkürler', 'parÃ aları': 'parçaları',
    'ilginÃ': 'ilginç', 'ilginÃ ': 'ilginç', 'gerÃ ekten': 'gerçekten',
    'Ã ok': 'çok', 'mÃ kemmel': 'mükemmel', 'sÃ per': 'süper', 'tÃ r': 'tür',
    'bötÃ n': 'bütün', 'düşÃ nerek': 'düşünerek', 'Ã ocuk': 'çocuk',
    'Ã ift': 'çift', 'sÃ rekli': 'sürekli', 'Ã stad': 'üstad', 'sÃ ven': 'söven',
    'gÃ re': 'göre', 'kÃ tÃ ': 'kötü', 'göldürsÃ n': 'güldürsün',
    'Ã alışan': 'çalışan', 'Ã ekmeye': 'çekmeye', 'Ã nereceğiniz': 'önereceğiniz',
    'Ã nerir': 'önerir', 'Ã döl': 'ödül', 'professyÃ nel': 'profesyonel',
    'yÃ celtilecek': 'yüceltilecek', 'görÃ rsÃ nöz': 'görürsünüz',
    'albümÃ ': 'albümü', 'albÃ m': 'albüm', 'parÃ alar': 'parçalar',
    # --- Add more pairs using the GARBLED characters as keys ---
}

# --- Optional: Log file for changes ---
LOG_FILE = 'db_comment_update_log.txt'

# --- Functions ---

def connect_db():
    """Establishes a PostgreSQL database connection."""
    conn = None
    print("Attempting to connect to PostgreSQL database...")
    try:
        conn = psycopg2.connect(DATABASE_URL)
        print("PostgreSQL connection successful.")
        return conn
    except psycopg2.OperationalError as e:
        print(f"Database Connection Error: {e}")
        print("Please check your DATABASE_URL, network connection, and DB server status.")
        return None # Return None instead of exiting
    except Exception as e:
        print(f"Database connection failed with an unexpected error: {e}")
        return None # Return None

def fetch_comments_to_fix(conn):
    """Fetches comments containing the GARBLED_CHAR in author or content."""
    results = []
    cursor = None
    print(f"Searching for comments with garbled character '{GARBLED_CHAR}'...")
    like_pattern = f'%{GARBLED_CHAR}%'

    try:
        cursor = conn.cursor()
        # Fetch ID, Author, Content for potential candidates
        comment_query = f"""
            SELECT {COMMENT_ID_COLUMN}, {COMMENT_AUTHOR_COLUMN}, {COMMENT_CONTENT_COLUMN}
            FROM {COMMENTS_TABLE}
            WHERE {COMMENT_AUTHOR_COLUMN} LIKE %s OR {COMMENT_CONTENT_COLUMN} LIKE %s
            ORDER BY {COMMENT_ID_COLUMN};
        """
        cursor.execute(comment_query, (like_pattern, like_pattern))
        results = cursor.fetchall() # Fetch all matching rows
        if results:
             print(f"Found {len(results)} potentially corrupted comments to process.")
        else:
            print("No potentially corrupted comments found matching the criteria.")
        return results

    except psycopg2.Error as e:
        print(f"Database query failed: {e}")
        return None # Indicate failure
    except Exception as e:
        print(f"An unexpected error occurred during query execution: {e}")
        return None
    finally:
        if cursor:
            cursor.close()

def build_regex_and_replace_func(word_map):
    """Builds regex and case-preserving replace function (from your script)."""
    # Use \b word boundaries for safer replacement
    pattern = r'\b(' + '|'.join(re.escape(key) for key in word_map.keys()) + r')\b'
    regex = re.compile(pattern, re.IGNORECASE | re.UNICODE)

    def replace_func(match):
        matched_word = match.group(1)
        found_key = None
        # Case-insensitive lookup in the map
        for key in word_map.keys():
            if matched_word.lower() == key.lower():
                found_key = key
                break
        if found_key is None:
            # print(f"Debug: No map key found for matched word '{matched_word}'") # Optional debug
            return matched_word # Return original if no key matches (e.g., substring match prevented by \b)

        replacement = word_map[found_key]

        # Preserve case
        if matched_word.istitle():
            return replacement.title()
        elif matched_word.isupper():
            return replacement.upper()
        else:
             return replacement
    return regex, replace_func

def apply_word_fixes_optimized(text, regex, replace_func):
    """Applies replacements using pre-compiled regex and function."""
    if text is None: return None # Handle potential NULL values from DB
    try:
        return regex.sub(replace_func, text)
    except Exception as e:
        print(f"Warning: Regex substitution failed for text chunk: '{text[:50]}...'. Error: {e}")
        return text # Return original text on error

# --- Main Execution Block ---
if __name__ == "__main__":
    start_run_time = time.time()

    # Pre-compile regex and replacement function for efficiency
    word_regex, word_replace_func = build_regex_and_replace_func(WORD_REPLACEMENT_MAP)

    conn = None
    processed_log = [] # To store details for the log file

    try:
        conn = connect_db()
        if not conn:
            sys.exit(1) # Exit if connection failed

        comments_to_process = fetch_comments_to_fix(conn)

        if not comments_to_process:
            print("No comments requiring fixes were found.")
            sys.exit(0)

        # --- Prepare for Updates ---
        updates_to_make = [] # Store tuples of (id, fixed_author, fixed_content)
        potential_fix_count = 0

        print("\nApplying word fixes in memory...")
        for comment_id, original_author, original_content in comments_to_process:
            fixed_author = apply_word_fixes_optimized(original_author, word_regex, word_replace_func)
            fixed_content = apply_word_fixes_optimized(original_content, word_regex, word_replace_func)

            log_entry = {
                'id': comment_id,
                'original_author': original_author, 'fixed_author': fixed_author,
                'original_content': original_content, 'fixed_content': fixed_content,
                'change_made': False
            }

            # Check if any actual change was made
            if original_author != fixed_author or original_content != fixed_content:
                updates_to_make.append((comment_id, fixed_author, fixed_content))
                log_entry['change_made'] = True
                potential_fix_count += 1

            processed_log.append(log_entry)

        print(f"Identified {potential_fix_count} comments with potential changes to apply.")

        if not updates_to_make:
            print("No actual changes needed after applying fixes.")
            sys.exit(0)

        # --- User Confirmation ---
        print("\n" + "="*30)
        print("      !!! WARNING !!!")
        print("This script will modify your database.")
        print(f"Attempting to UPDATE {potential_fix_count} rows in the '{COMMENTS_TABLE}' table.")
        print("MAKE SURE YOU HAVE A DATABASE BACKUP!")
        print("="*30 + "\n")
        proceed = input("Proceed with database update? (yes/no): ").strip().lower()

        if proceed != 'yes':
            print("Database update cancelled by user.")
            sys.exit(0)

        # --- Perform Database Updates ---
        print("\n--- Starting Database Update ---")
        cursor = None
        updated_count = 0
        failed_count = 0
        try:
            cursor = conn.cursor()
            # Prepare SQL Statement (Uses %s for psycopg2 placeholders)
            sql_update = f"""
                UPDATE {COMMENTS_TABLE}
                SET {COMMENT_AUTHOR_COLUMN} = %s,
                    {COMMENT_CONTENT_COLUMN} = %s
                WHERE {COMMENT_ID_COLUMN} = %s
            """
            print(f"Executing UPDATE statements...")

            for comment_id, fixed_author, fixed_content in updates_to_make:
                try:
                    # Order of params must match SET columns, then WHERE column
                    params = (fixed_author, fixed_content, comment_id)
                    cursor.execute(sql_update, params)
                    # Check if the update affected a row
                    if cursor.rowcount > 0:
                        updated_count += 1
                        # print(f"  Successfully updated comment ID: {comment_id}") # Verbose logging
                    else:
                         print(f"  Warning: Update for comment ID {comment_id} affected 0 rows (ID might not exist?).")
                         failed_count += 1
                except psycopg2.Error as db_error:
                    print(f"  Error updating comment ID {comment_id}: {db_error}")
                    conn.rollback() # Rollback immediately on error within the loop
                    failed_count += 1
                    print("Rolled back transaction due to error.")
                    break # Stop processing further updates on error
                except Exception as e:
                    print(f"  Unexpected error updating comment ID {comment_id}: {e}")
                    conn.rollback() # Rollback immediately
                    failed_count += 1
                    print("Rolled back transaction due to unexpected error.")
                    break # Stop processing

            # Commit only if the loop completed without breaking due to errors
            if failed_count == 0:
                print("\nAttempting to commit changes...")
                conn.commit()
                print("Database changes committed successfully.")
            else:
                print(f"\nDatabase update finished with {failed_count} errors. Changes were rolled back.")

        except Exception as e:
            print(f"\nAn overall error occurred during database update phase: {e}")
            if conn:
                print("Rolling back any potential partial changes.")
                conn.rollback()
        finally:
            if cursor:
                cursor.close()

    except Exception as e:
        # Catch errors during connection, fetching, or processing phases
        print(f"\nAn unexpected error occurred: {e}")
        traceback.print_exc() # Print full traceback for debugging
        if conn: # Attempt rollback if connection existed
             try: conn.rollback()
             except: pass # Ignore rollback errors if connection already closed/bad
    finally:
        if conn:
            conn.close()
            print("\nDatabase connection closed.")

    # --- Write Log File ---
    print(f"\nWriting processing log to '{LOG_FILE}'...")
    try:
        with open(LOG_FILE, 'w', encoding='utf-8') as f:
            f.write(f"# Comment Update Log - {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# Searched for comments containing: '{GARBLED_CHAR}'\n")
            f.write(f"# Database Update Summary: Attempted={potential_fix_count}, Succeeded={updated_count}, Failed/RolledBack={failed_count}\n\n")

            for entry in processed_log:
                 f.write(f"Comment ID: {entry['id']}\n")
                 f.write(f"Change Applied: {'Yes' if entry['change_made'] else 'No'}\n")
                 f.write(f"Original Author : {entry.get('original_author', 'N/A')}\n")
                 if entry['change_made']:
                     f.write(f"Fixed Author    : {entry.get('fixed_author', 'N/A')}\n")
                 f.write(f"Original Content: {entry.get('original_content', 'N/A')}\n")
                 if entry['change_made']:
                    f.write(f"Fixed Content   : {entry.get('fixed_content', 'N/A')}\n")
                 f.write("---\n")
            print(f"Successfully saved processing log to '{LOG_FILE}'.")
    except IOError as e:
        print(f"Error writing log file '{LOG_FILE}': {e}")
    except Exception as e:
        print(f"An unexpected error occurred during log file writing: {e}")


    end_run_time = time.time()
    print(f"\nScript finished in {end_run_time - start_run_time:.2f} seconds.")