# preview_encoding_fix_v7.py
import os
import sys
import psycopg2 # <-- Added missing import
from dotenv import load_dotenv
import re

# --- Configuration ---
load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL') # <-- Moved assignment outside try block

# --- V7 Replacement Strategy ---
# Focus on mapping individual garbled chars or short sequences derived from examples
# Order matters: longer/more specific sequences first.
REPLACEMENT_MAP_V7 = {
    # --- Double Encoding Patterns (Keep these) ---
    'ÃƒÂ¶': 'ö', 'ÃƒÂ¼': 'ü', 'ÃƒÂ§': 'ç', 'ÃƒÂ°': 'ğ', 'ÃƒÂ½': 'ı',
    'Ã„Â°': 'İ', 'Ã…Å¸': 'ş', 'Ã…Å¾': 'Ş', 'ÃƒÂŸ': 'Ğ',

    # --- Observed Multi-Byte Garbles -> Single Turkish Char ---
    # Based on "özümsemiş" -> Ã �zÃ �msemiÅŸ
    'Ã �z': 'öz', 'Ã �m': 'üm', 'iÅŸ': 'iş',

    # Based on "rock’ı" -> rock’Ä �
    'Ä �': 'ı',

    # Based on "lâkin" -> lÃ �kin
    'lÃ ': 'lâ',

    # Based on "işte" -> Ä �ÅŸte
    'Ä �ÅŸ': 'iş',

    # Based on "ölüyorum" -> Ã �lÃ �yorum
    'Ã �l': 'öl', 'Ã �y': 'üy',

    # Based on "için" -> iÃ �in
    'iÃ ': 'iç',

    # Based on "geçerli" -> geÃ �erli
    'eÃ ': 'eç',

    # Based on "günlerinden" -> gÃ �nlerinden
    'gÃ ': 'gü',

    # Based on "başladım" -> baÅŸladÄ �m
    'aÅŸ': 'aş',

    # Based on "böyle" -> bÃ �yle
    'bÃ ': 'bö',

    # Based on "rastlamış" -> rastlamÄ �ÅŸ
    'Ä �ÅŸ': 'ış',

    # Based on "acılar" -> acÄ �lar
    # Covered by 'Ä �': 'ı'

    # Based on "yaşamadığınız" -> yaÅŸamadÄ �ÄŸÄ �nÄ �z
    # Covered by 'aÅŸ', 'Ä �', 'ÄŸ'

    # Based on "açık" -> aÃ �Ä �k
    'aÃ ': 'aç',

    # Based on "dünya" -> dÃ �nya
    'dÃ ': 'dü',

    # Include specific multi-word fixes from V6 if they were very accurate
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

    # --- General Single Mojibake Mappings (Fallbacks) ---
    'ÄŸ': 'ğ', 'Äž': 'Ğ',
    'ÅŸ': 'ş', 'Åž': 'Ş',
    'Ä±': 'ı', 'Ä°': 'İ',
    'Ã¶': 'ö', 'Ã–': 'Ö',
    'Ã§': 'ç', 'Ã‡': 'Ç',
    'Ã¼': 'ü', 'Ãœ': 'Ü',
    'Ä ': 'ı',   # Ä followed by space -> ı
    'Ä\xa0': 'ı', # Ä followed by non-breaking space
    'Ä ': 'ı',   # Duplicate space just in case

    # --- Punctuation ---
    'â€™': '’', 'â€œ': '“', 'â€�': '”',
}


# --- Functions ---
def apply_fixes_py_v7(text, replacement_map):
    """Applies replacements using the character/short-sequence map (V7)."""
    if text is None: return None
    fixed_text = text
    # Apply longer sequences first
    sorted_keys = sorted(replacement_map.keys(), key=len, reverse=True)
    for find in sorted_keys:
        replace = replacement_map[find]
        fixed_text = fixed_text.replace(find, replace)
    return fixed_text


# --- Main Execution Block (Use V7 Map and Function) ---
if __name__ == "__main__":
    # Check for DATABASE_URL early
    if not DATABASE_URL:
        print("!!! Configuration Error: DATABASE_URL environment variable not set.")
        sys.exit(1) # Exit if DB URL is missing

    while True:
        try:
            post_id_input = input("Enter the Post ID to preview encoding fixes for (using V7 Char Map): ")
            post_id = int(post_id_input)
            break
        except ValueError:
            print("Invalid input. Please enter a number for the Post ID.")

    print("\n--- Previewing Encoding Fixes (V7 - Character/Short Sequence Map) ---")
    print("--- (This script DOES NOT modify the database) ---")

    conn = None
    cursor = None
    try:
        print(f"Connecting to database...")
        conn = psycopg2.connect(DATABASE_URL) # Connect using the global DATABASE_URL
        cursor = conn.cursor()
        print("Database connection successful.")

        print(f"\nFetching post details for ID: {post_id}")
        cursor.execute("SELECT id, title, timestamp FROM posts WHERE id = %s", (post_id,))
        post_result = cursor.fetchone()

        if not post_result:
            print(f"!!! Post with ID {post_id} not found.")
            sys.exit()

        post_db_id, post_title, post_timestamp = post_result
        # Use V7 function for preview
        fixed_post_title = apply_fixes_py_v7(post_title, REPLACEMENT_MAP_V7)

        print("-" * 20)
        print(f"Post ID: {post_db_id}")
        print(f"Original Title:      {post_title}")
        print(f"Preview Fixed Title: {fixed_post_title}")
        print(f"Timestamp:           {post_timestamp}")
        print("-" * 20)

        print(f"\nFetching comments for Post ID: {post_id}")
        cursor.execute(
            "SELECT id, author, comment_date, comment_time, comment_number, content FROM comments WHERE post_id = %s ORDER BY id",
            (post_id,)
        )
        comments = cursor.fetchall()

        if not comments:
            print("No comments found for this post.")
        else:
            print(f"Found {len(comments)} comments. Displaying preview:\n")
            for comment in comments:
                comm_id, comm_author, comm_date, comm_time, comm_num, comm_content = comment

                # Use V7 function for preview
                fixed_author = apply_fixes_py_v7(comm_author, REPLACEMENT_MAP_V7)
                fixed_content = apply_fixes_py_v7(comm_content, REPLACEMENT_MAP_V7)

                print("~" * 60)
                print(f"Comment #{comm_num} (ID: {comm_id})")
                print(f"Author:   {comm_author}  ->  Preview Fixed: {fixed_author}")
                print(f"Date/Time:{comm_date} {comm_time}")
                print("-" * 10 + " Original Content " + "-" * 10)
                print(comm_content)
                print("-" * 10 + " Preview Fixed Content (V7 Map) " + "-" * 10)
                print(fixed_content)
                print("~" * 60 + "\n")

        print("\n--- Preview complete. Database was NOT modified. ---")

    # Keep specific error handling for OperationalError
    except psycopg2.OperationalError as e:
        print(f"!!! Database Connection Error: {e}")
        print("Please check your DATABASE_URL, network connection, and RDS security group settings.")
    except Exception as e:
        print(f"!!! An unexpected error occurred: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
            print("\nDatabase connection closed.")