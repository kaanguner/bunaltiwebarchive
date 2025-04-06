import os
import sys
import psycopg2 # Ensure this is installed: pip install psycopg2-binary
from dotenv import load_dotenv
import time

# --- Configuration ---
load_dotenv() # Load environment variables from .env file

# Get database URL from environment variable
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    print("Error: DATABASE_URL environment variable not set.")
    print("Please create a .env file with DATABASE_URL='postgresql://user:password@host:port/database'")
    sys.exit(1)

# --- Table and Column Names (Adjust if necessary) ---
# Assuming the structure based on your preview script
POSTS_TABLE = 'posts'
POST_ID_COLUMN = 'id'
POST_TITLE_COLUMN = 'title'

COMMENTS_TABLE = 'comments'
COMMENT_ID_COLUMN = 'id'          # Primary key of the comments table
COMMENT_POST_ID_COLUMN = 'post_id' # Foreign key linking comments to posts
COMMENT_AUTHOR_COLUMN = 'author'
COMMENT_CONTENT_COLUMN = 'content'

# --- Output File ---
OUTPUT_FILE = 'comments_with_garbled_A_char.txt'

# --- The Specific Garbled Character to Find ---
# We are looking for the single character 'Ã' (Unicode U+00C3)
GARBLED_CHAR = 'Ã'

# --- !!! --- End of Configuration --- !!! ---

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
        sys.exit(1)
    except Exception as e:
        print(f"Database connection failed with an unexpected error: {e}")
        sys.exit(1)

def fetch_corrupted_data(conn):
    """
    Fetches IDs and content containing the GARBLED_CHAR
    from both post titles and comment content/authors.
    """
    results = {'posts': [], 'comments': []}
    cursor = None
    print(f"Searching for garbled character '{GARBLED_CHAR}'...")

    try:
        cursor = conn.cursor()

        # --- Fetch from Posts ---
        post_query = f"""
            SELECT {POST_ID_COLUMN}, {POST_TITLE_COLUMN}
            FROM {POSTS_TABLE}
            WHERE {POST_TITLE_COLUMN} LIKE %s
            ORDER BY {POST_ID_COLUMN};
        """
        # Parameter for LIKE needs wildcards included
        like_pattern = f'%{GARBLED_CHAR}%'

        cursor.execute(post_query, (like_pattern,))
        post_results = cursor.fetchall()
        if post_results:
            print(f"Found {len(post_results)} potentially corrupted post titles.")
            results['posts'] = post_results
        else:
            print("No potentially corrupted post titles found.")


        # --- Fetch from Comments ---
        # Search in both author and content fields
        comment_query = f"""
            SELECT {COMMENT_ID_COLUMN}, {COMMENT_AUTHOR_COLUMN}, {COMMENT_CONTENT_COLUMN}
            FROM {COMMENTS_TABLE}
            WHERE {COMMENT_AUTHOR_COLUMN} LIKE %s OR {COMMENT_CONTENT_COLUMN} LIKE %s
            ORDER BY {COMMENT_ID_COLUMN};
        """
        cursor.execute(comment_query, (like_pattern, like_pattern))
        comment_results = cursor.fetchall()
        if comment_results:
             print(f"Found {len(comment_results)} potentially corrupted comments (author or content).")
             results['comments'] = comment_results
        else:
            print("No potentially corrupted comments found.")

        return results

    except psycopg2.Error as e:
        print(f"Database query failed: {e}")
        # Optional: Rollback if necessary, though SELECT shouldn't need it
        # conn.rollback()
        return None # Indicate failure
    except Exception as e:
        print(f"An unexpected error occurred during query execution: {e}")
        return None
    finally:
        if cursor:
            cursor.close()


# --- Main Execution Block ---
if __name__ == "__main__":
    start_run_time = time.time()
    conn = connect_db()

    if conn:
        fetched_data = fetch_corrupted_data(conn)
        conn.close() # Close connection once data is fetched
        print("\nDatabase connection closed.")

        if fetched_data is not None:
            total_posts = len(fetched_data['posts'])
            total_comments = len(fetched_data['comments'])
            print(f"\nTotal potentially corrupted items found: Posts={total_posts}, Comments={total_comments}")

            if total_posts == 0 and total_comments == 0:
                print("No data containing the garbled character found.")
                sys.exit(0)

            # --- Write to File ---
            print(f"\nWriting results to '{OUTPUT_FILE}'...")
            try:
                with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                    f.write(f"# Data extracted on: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"# Searching for character: '{GARBLED_CHAR}'\n\n")

                    if fetched_data['posts']:
                        f.write("--- Potentially Corrupted Post Titles ---\n")
                        for post_id, title in fetched_data['posts']:
                            f.write(f"Post ID: {post_id}\n")
                            f.write(f"Title: {title}\n")
                            f.write("---\n")
                        f.write("\n")

                    if fetched_data['comments']:
                        f.write("--- Potentially Corrupted Comments ---\n")
                        for comm_id, author, content in fetched_data['comments']:
                            f.write(f"Comment ID: {comm_id}\n")
                            f.write(f"Author: {author}\n")
                            f.write(f"Content: {content}\n")
                            f.write("---\n")
                        f.write("\n")

                print(f"Successfully saved data to '{OUTPUT_FILE}'.")

            except IOError as e:
                print(f"Error writing to file '{OUTPUT_FILE}': {e}")
            except Exception as e:
                print(f"An unexpected error occurred during file writing: {e}")

    end_run_time = time.time()
    print(f"\nScript finished in {end_run_time - start_run_time:.2f} seconds.")