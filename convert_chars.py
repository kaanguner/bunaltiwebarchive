# fix_encoding_db_v7b.py (Two Connections)
import os
import sys
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
from tqdm import tqdm
import re

# --- Configuration ---
load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')
REPLACEMENT_MAP_V7 = {
    # --- PASTE YOUR FULL REPLACEMENT_MAP_V7 HERE ---
    # (Same map as before)
    'ÃƒÂ¶': 'ö', 'ÃƒÂ¼': 'ü', 'ÃƒÂ§': 'ç', 'ÃƒÂ°': 'ğ', 'ÃƒÂ½': 'ı',
    'Ã„Â°': 'İ', 'Ã…Å¸': 'ş', 'Ã…Å¾': 'Ş', 'ÃƒÂŸ': 'Ğ',
    'Ã �alÄ �ÅŸtÄ �ramÄ �yorum': 'çalıştıramıyorum',
    'uzantÄ �sÄ �nÄ �': 'uzantısını',
    'indirdiÄŸimiz': 'indirdiğimiz',
    'Ã �oÄŸu': 'Çoğu',
    'meraklÄ �lara': 'meraklılara',
    'yarÄ �sÄ �': 'yarısı',
    'Ã �almÄ �ÅŸ': 'çalmış',
    'gÃ �rÃ �nce': 'görünce',
    'gÃ �remiyorum': 'göremiyorum',
    'albÃ �mleri': 'albümleri',
    'Ã �ekti': 'çekti',
    'Ã �nce': 'önce',
    'Ã �teki': 'öteki',
    'Ã � olsa': 'ü olsa',
    'aÃ �ar': 'açar',
    'dÃ �ÅŸsÃ �n': 'düşsün',
    'gÃ �neymiÅŸ': 'güneymiş',
    'albÃ �m': 'albüm',
    'tÃ �re': 'türe',
    'geÃ � oldu': 'geç oldu',
    'kÄ �smÄ �na': 'kısmına',
    'yazÄ �n': 'yazın',
    'sakÄ �n': 'sakın',
    'olsaydÄ �': 'olsaydı',
    'dosyalÄ �': 'dosyalı',
    'yorumlarÄ �': 'yorumları',
    'hayatÄ �mÄ �': 'hayatımı',
    'postlarÄ �nda': 'postlarında',
    'kaydÄ �rdÄ �': 'kaydırdı',
    'aynÄ �': 'aynı',
    'bayaÄŸÄ �': 'bayağı',
    'anlÄ �k': 'anlık',
    'olduÄŸunuz': 'olduğunuz',
    'acÄ �lar': 'acılar',
    'yaratÄ �p': 'yaratıp',
    'yaÅŸamadÄ �ÄŸÄ �nÄ �z': 'yaşamadığınız',
    'kapayÄ �': 'kapıyı',
    'aÃ �andÄ �r': 'açandır',
    'gÃ �zÃ �mde': 'gözümde',
    'harmanlamÄ �ÅŸlar': 'harmanlamışlar',
    'olunmalÄ �': 'olunmalı',
    'kullanÄ �yolar': 'kullanıyolar',
    'baÄŸÄ �mlÄ �lÄ �k': 'bağımlılık',
    'yarattÄ �klarÄ �': 'yarattıkları',
    'demiÅŸim': 'demişim',
    'bulursanÄ �z': 'bulursanız',
    'rÃ �ya': 'rüya',
    'diÄŸer': 'diğer',
    'kayÄ �tlarÄ �nÄ �': 'kayıtlarını',
    'beÄŸenmeyeceksinizdir': 'beğenmeyeceksinizdir',
    'ÄŸ': 'ğ', 'Äž': 'Ğ',
    'ÅŸ': 'ş', 'Åž': 'Ş',
    'Ä±': 'ı', 'Ä°': 'İ',
    'Ã¶': 'ö', 'Ã–': 'Ö',
    'Ã§': 'ç', 'Ã‡': 'Ç',
    'Ã¼': 'ü', 'Ãœ': 'Ü',
    'Ä ': 'ı',
    'Ä\xa0': 'ı',
    'Ä ': 'ı',
    'â€™': '’', 'â€œ': '“', 'â€�': '”',
}

BATCH_SIZE = 500

# --- Functions ---
def apply_fixes_py_v7(text, replacement_map):
    """Applies replacements using the character/short-sequence map (V7)."""
    if text is None: return None
    fixed_text = text
    sorted_keys = sorted(replacement_map.keys(), key=len, reverse=True)
    for find in sorted_keys:
        replace = replacement_map[find]
        fixed_text = fixed_text.replace(find, replace)
    return fixed_text

def fix_table_column_v7_two_conn(read_conn, write_conn, table_name, column_name, pk_column, replacement_map):
    """Uses separate connections for reading (named cursor) and writing."""
    print(f"\n--- Fixing table '{table_name}', column '{column_name}' using V7 Map (Two Connections) ---")
    read_cursor = None
    updated_count = 0
    processed_count = 0
    # Build LIKE patterns (same as before)
    like_patterns = set()
    for key in replacement_map.keys():
        if key and key[0] in 'ÃÅÄâ':
             escaped_key_part = key[0].replace('%', '\\%').replace('_', '\\_')
             like_patterns.add(f"{column_name} LIKE '%{escaped_key_part}%'")
    if not like_patterns: where_clause = "1=1"
    else: where_clause = " OR ".join(like_patterns)

    try:
        # Use named cursor on the read connection (NO autocommit needed here)
        read_cursor = read_conn.cursor(name=f'fetch_{table_name}_{column_name}_v7')
        sql_select = f"SELECT {pk_column}, {column_name} FROM {table_name} WHERE {where_clause}"
        read_cursor.execute(sql_select)
        print(f"Fetching rows from '{table_name}' matching potential encoding patterns...")

        while True:
            rows_to_update = []
            results = read_cursor.fetchmany(BATCH_SIZE)
            if not results: break

            processed_count += len(results)
            print(f"Processing batch of {len(results)} rows (Total checked: {processed_count})...")

            for row_pk, original_text in tqdm(results, desc="Applying V7 fixes"):
                if original_text:
                    fixed_text = apply_fixes_py_v7(original_text, replacement_map)
                    if fixed_text != original_text:
                        rows_to_update.append((fixed_text, row_pk))

            # Update using the *separate* write connection
            if rows_to_update:
                print(f"Updating {len(rows_to_update)} rows via write connection...")
                # Use a standard cursor for writing on the write connection
                with write_conn.cursor() as write_cursor:
                    update_sql = f"UPDATE {table_name} SET {column_name} = %s WHERE {pk_column} = %s"
                    psycopg2.extras.execute_batch(write_cursor, update_sql, rows_to_update, page_size=BATCH_SIZE)
                    # Commit changes on the write connection
                    write_conn.commit()
                    updated_count += len(rows_to_update)
                # No write_cursor.close() needed with 'with' statement

        print(f"Finished processing '{table_name}.{column_name}'. Total rows updated: {updated_count} out of {processed_count} checked.")

    except psycopg2.Error as e:
        print(f"!!! Database error occurred for {table_name}.{column_name}: {e}")
        # Rollback might not be needed if write_conn auto-commits or handles errors
        # Ensure write_conn is rolled back if an error happens DURING batch execution
        if write_conn: write_conn.rollback() # Rollback the write connection just in case
        print(f"Skipping further fixes for {table_name}.{column_name} due to error.")
    except Exception as e:
        print(f"!!! An unexpected error occurred for {table_name}.{column_name}: {e}")
        if write_conn: write_conn.rollback()
        print(f"Skipping further fixes for {table_name}.{column_name} due to error.")
    finally:
        if read_cursor: read_cursor.close() # Close the named read cursor


def rebuild_user_stats(conn):
    """Drops and rebuilds the user_stats table."""
    # (Same implementation as before - uses its own cursor/transaction)
    print("\n--- Rebuilding 'user_stats' table ---")
    cursor = None
    try:
        cursor = conn.cursor()
        print("Dropping existing user_stats table (if exists)...")
        cursor.execute("DROP TABLE IF EXISTS user_stats;")
        print("Creating new user_stats table from comments...")
        cursor.execute('''
            CREATE TABLE user_stats AS SELECT ... (rest of query same as before) ...
        ''') # Shortened for brevity
        cursor.execute("ALTER TABLE user_stats ADD PRIMARY KEY (username);")
        conn.commit()
        print("Successfully rebuilt 'user_stats' table.")
    # ... (rest of error handling same as before) ...
    finally:
        if cursor: cursor.close()

# --- Main Execution ---
if __name__ == "__main__":
    print("Starting database encoding fix process using V7 Map (Two Connections)...")
    print("="*60)
    print("!!! FINAL WARNING: HAVE YOU BACKED UP YOUR DATABASE? !!!")
    # ... (rest of warnings same as before) ...
    print("="*60)

    confirm = input("Type 'YES' to confirm you have a backup and wish to proceed: ")
    if confirm != 'YES': print("Operation cancelled."); sys.exit()

    read_conn = None
    write_conn = None
    try:
        print(f"Connecting to database (read & write connections)...")
        if not DATABASE_URL: raise ValueError("DATABASE_URL not set.")

        read_conn = psycopg2.connect(DATABASE_URL)
        write_conn = psycopg2.connect(DATABASE_URL)
        # Optional: Set autocommit on write connection if preferred, but manual commit is safer
        # write_conn.autocommit = True
        print("Database connections successful.")

        # --- Apply Fixes ---
        print(">>> Fixing comments.content...")
        fix_table_column_v7_two_conn(read_conn, write_conn, 'comments', 'content', 'id', REPLACEMENT_MAP_V7)

        print("\n>>> Fixing posts.title...")
        fix_table_column_v7_two_conn(read_conn, write_conn, 'posts', 'title', 'id', REPLACEMENT_MAP_V7)

        # --- Optional: Fix Author Names ---
        print("\n>>> Optional: Fixing author names (requires user_stats rebuild)")
        fix_author = input("Fix 'comments.author' and rebuild 'user_stats'? (yes/no): ").lower()
        if fix_author == 'yes':
             print("Fixing comments.author...")
             # Pass the connections to the fix function
             fix_table_column_v7_two_conn(read_conn, write_conn, 'comments', 'author', 'id', REPLACEMENT_MAP_V7)
             # Rebuild stats using the write connection (or either, as it manages its own transaction)
             rebuild_user_stats(write_conn)
        else:
             print("Skipping author name fixes and user_stats rebuild.")

        print("\n--- Encoding fix process using V7 Map completed. ---")
        print("--- Please verify the results on your website. ---")

    # ... (rest of error handling same as before) ...
    finally:
        # Close both connections
        if read_conn: read_conn.close(); print("\nRead connection closed.")
        if write_conn: write_conn.close(); print("Write connection closed.")