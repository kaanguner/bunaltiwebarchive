import re
import os
import sys
import time

# --- Corrected High-Confidence Word Replacement Map (V3) ---
# Keys use ACTUAL GARBLED characters. Values are correct lowercase Turkish.
WORD_REPLACEMENT_MAP = {
    'gerÃekten': 'gerçekten',
    'Ãok': 'çok',           # Corrected key: Uses Ã
    'mÃkemmel': 'mükemmel', # Corrected key: Uses Ã
    'sÃper': 'süper',       # Corrected key: Uses Ã
    'tÃr': 'tür',           # Corrected key: Uses Ã
    'bötÃn': 'bütün',       # Corrected key: Uses Ã
    'gözel': 'güzel',       # Potential typo/corruption
    'mözik': 'müzik',       # Potential typo/corruption
    'düşÃnerek': 'düşünerek', # Corrected key: Uses Ã
    'yözden': 'yüzden',     # Potential typo/corruption
    'Ãocuk': 'çocuk',       # Corrected key: Uses Ã
    'Ãift': 'çift',         # Corrected key: Uses Ã
    'sÃrekli': 'sürekli',   # Corrected key: Uses Ã
    'Ãstad': 'üstad',       # Corrected key: Uses Ã
    'sÃven': 'söven',       # Corrected key: Uses Ã (assuming from sÃ ven sample)
    'gÃre': 'göre',         # Corrected key: Uses Ã
    'kÃtÃ': 'kötü',         # Corrected key: Uses Ã twice
    'göldürsÃn': 'güldürsün', # Corrected key: Uses Ã
    'Ãalışan': 'çalışan',   # Corrected key: Uses Ã
    'Ãekmeye': 'çekmeye',   # Corrected key: Uses Ã
    'Ãnereceğiniz': 'önereceğiniz', # Corrected key: Uses Ã
    'Ãnerir': 'önerir',     # Corrected key: Uses Ã
    'Ãdöl': 'ödül',         # Corrected key: Uses Ã
    'professyÃnel': 'profesyonel', # Corrected key: Uses Ã
    'yÃceltilecek': 'yüceltilecek', # Corrected key: Uses Ã
    'görÃrsÃnöz': 'görürsünüz', # Corrected key: Uses Ã twice
    'albümÃ': 'albümü',     # Corrected key: Uses Ã
    'albÃm': 'albüm',       # Corrected key: Uses Ã
    'parÃalar': 'parçalar', # *** ADDED THIS MAPPING ***
    'teşekkÃ rler': 'teşekkürler',
    'parÃ aları': 'parçaları',
    'ilginÃ': 'ilginç',
    'ilginÃ ': 'ilginç',
    'gerÃ ekten': 'gerçekten',
    'Ã ok': 'çok',           # Corrected key: Uses Ã 
    'mÃ kemmel': 'mükemmel', # Corrected key: Uses Ã 
    'sÃ per': 'süper',       # Corrected key: Uses Ã 
    'tÃ r': 'tür',           # Corrected key: Uses Ã 
    'bötÃ n': 'bütün',       # Corrected key: Uses Ã 
    'gözel': 'güzel',       # Potential typo/corruption
    'mözik': 'müzik',       # Potential typo/corruption
    'düşÃ nerek': 'düşünerek', # Corrected key: Uses Ã 
    'yözden': 'yüzden',     # Potential typo/corruption
    'Ã ocuk': 'çocuk',       # Corrected key: Uses Ã 
    'Ã ift': 'çift',         # Corrected key: Uses Ã 
    'sÃ rekli': 'sürekli',   # Corrected key: Uses Ã 
    'Ã stad': 'üstad',       # Corrected key: Uses Ã 
    'sÃ ven': 'söven',       # Corrected key: Uses Ã  (assuming from sÃ  ven sample)
    'gÃ re': 'göre',         # Corrected key: Uses Ã 
    'kÃ tÃ ': 'kötü',         # Corrected key: Uses Ã  twice
    'göldürsÃ n': 'güldürsün', # Corrected key: Uses Ã 
    'Ã alışan': 'çalışan',   # Corrected key: Uses Ã 
    'Ã ekmeye': 'çekmeye',   # Corrected key: Uses Ã 
    'Ã nereceğiniz': 'önereceğiniz', # Corrected key: Uses Ã 
    'Ã nerir': 'önerir',     # Corrected key: Uses Ã 
    'Ã döl': 'ödül',         # Corrected key: Uses Ã 
    'professyÃ nel': 'profesyonel', # Corrected key: Uses Ã 
    'yÃ celtilecek': 'yüceltilecek', # Corrected key: Uses Ã 
    'görÃ rsÃ nöz': 'görürsünüz', # Corrected key: Uses Ã  twice
    'albümÃ ': 'albümü',     # Corrected key: Uses Ã 
    'albÃ m': 'albüm',       # Corrected key: Uses Ã 
    'parÃ alar': 'parçalar', # *** ADDED THIS MAPPING ***
    # --- Add more pairs using the GARBLED characters as keys ---
}

# --- Input/Output Files ---
INPUT_FILE = 'comments_with_garbled_A_char.txt' # From extraction script
OUTPUT_FILE = 'comments_only_word_fixed_v3.txt' # New output file name

# --- Functions ---

def build_regex_and_replace_func(word_map):
    """Builds a single regex for all keys and a case-preserving replace function."""
    # *** Use \b word boundaries ***
    pattern = r'\b(' + '|'.join(re.escape(key) for key in word_map.keys()) + r')\b'
    # Compile with IGNORECASE
    regex = re.compile(pattern, re.IGNORECASE | re.UNICODE)

    def replace_func(match):
        """Looks up the replacement and preserves original case."""
        matched_word = match.group(1) # Group 1 contains the actual matched word

        # --- Case-insensitive lookup ---
        found_key = None
        for key in word_map.keys():
            if matched_word.lower() == key.lower(): # Compare lowercase versions
                found_key = key
                break

        if found_key is None:
            print(f"Warning: No map key found for matched word '{matched_word}'")
            return matched_word

        replacement = word_map[found_key]

        # Preserve case based on the *original matched word*
        if matched_word.istitle():
            return replacement.title()
        elif matched_word.isupper():
            return replacement.upper()
        else:
             return replacement

    return regex, replace_func

def apply_word_fixes_optimized(text, regex, replace_func):
    """Applies replacements using pre-compiled regex and replace function."""
    if text is None: return None
    try:
        return regex.sub(replace_func, text)
    except Exception as e:
        print(f"Warning: Regex substitution failed for text chunk: '{text[:50]}...'. Error: {e}")
        return text

def parse_input_file(filename):
    """Parses the input file into a list of dictionaries."""
    # (Using the same robust parsing function as last time)
    data = []
    current_entry = None
    entry_type = None

    if not os.path.exists(filename):
        print(f"Error: Input file '{filename}' not found.")
        sys.exit(1)

    print(f"Reading data from '{filename}'...")
    with open(filename, 'r', encoding='utf-8') as f:
        buffer = {}
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            if line == "---":
                if buffer:
                    if buffer.get('type') == 'comment':
                        if 'id' in buffer and 'content' in buffer:
                            data.append(buffer.copy())
                        else:
                            print(f"Warning: Skipping incomplete comment entry near ID {buffer.get('id')}.")
                    buffer = {}
                continue

            try:
                key, value = line.split(":", 1)
                key = key.strip().lower().replace(' ', '_')
                value = value.strip()

                if not buffer:
                     if key == 'post_id':
                         buffer['type'] = 'post'
                         buffer['id'] = int(value)
                     elif key == 'comment_id':
                         buffer['type'] = 'comment'
                         buffer['id'] = int(value)
                     else:
                         continue

                if key in ['title', 'author', 'content']:
                     # Handle potential multi-line content (simple approach: append)
                    if key == 'content' and 'content' in buffer:
                        buffer['content'] += "\n" + value
                    else:
                        buffer[key] = value
                elif key == 'comment_id' and buffer.get('type') == 'comment':
                     buffer['id'] = int(value)

            except ValueError:
                if buffer and 'content' in buffer and buffer.get('type') == 'comment':
                    buffer['content'] += "\n" + line
                else:
                     print(f"Warning: Skipping malformed line: {line}")

        if buffer and buffer.get('type') == 'comment' and 'id' in buffer and 'content' in buffer:
            data.append(buffer.copy())

    print(f"Parsed {len(data)} comment entries.")
    return data

# --- Main Execution Block ---
if __name__ == "__main__":
    start_run_time = time.time()

    # Pre-compile regex and replacement function for efficiency
    word_regex, word_replace_func = build_regex_and_replace_func(WORD_REPLACEMENT_MAP)

    # Parse only comments from the input file
    parsed_comments = parse_input_file(INPUT_FILE)

    if not parsed_comments:
        print("No comment data parsed from the input file. Exiting.")
        sys.exit(0)

    print(f"\nApplying word-level fixes (V3 Map) to {len(parsed_comments)} comments...")
    processed_comments = []
    fix_count = 0

    for comment in parsed_comments:
        processed_entry = comment.copy()
        made_change = False

        original_author = comment.get('author')
        original_content = comment.get('content')

        fixed_author = apply_word_fixes_optimized(original_author, word_regex, word_replace_func)
        fixed_content = apply_word_fixes_optimized(original_content, word_regex, word_replace_func)

        processed_entry['original_author'] = original_author
        processed_entry['fixed_author'] = fixed_author
        processed_entry['original_content'] = original_content
        processed_entry['fixed_content'] = fixed_content

        if original_author != fixed_author or original_content != fixed_content:
            made_change = True
            fix_count += 1

        processed_comments.append(processed_entry)

    print(f"Applied potential word fixes to {fix_count} comments.")

    # --- Write Processed Comment Data to Output File ---
    print(f"\nWriting word-fixed results to '{OUTPUT_FILE}'...")
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write(f"# Word-fixed comment data generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# Applied high-confidence word replacements (V3 Map).\n\n")

            for entry in processed_comments:
                 f.write(f"Comment ID: {entry['id']}\n")
                 # f.write(f"Original Author: {entry.get('original_author', 'N/A')}\n")
                 # f.write(f"Word Fixed Author: {entry.get('fixed_author', 'N/A')}\n")
                 f.write(f"Original Content: {entry.get('original_content', 'N/A')}\n")
                 f.write(f"Word Fixed Content: {entry.get('fixed_content', 'N/A')}\n")
                 f.write("---\n")

            print(f"Successfully saved word-fixed comment data to '{OUTPUT_FILE}'.")

    except IOError as e:
        print(f"Error writing to file '{OUTPUT_FILE}': {e}")
    except Exception as e:
        print(f"An unexpected error occurred during file writing: {e}")

    end_run_time = time.time()
    print(f"\nScript finished in {end_run_time - start_run_time:.2f} seconds.")

    # --- Optional: Print a sample comparison ---
    if processed_comments:
        print("\n--- Sample Comparison (First few comments) ---")
        for i, entry in enumerate(processed_comments[:20]): # Show first 5
             print(f"\nComment ID: {entry['id']}")
             # print(f"Original Author:  {entry['original_author']}") # Uncomment to see author changes
             # print(f"Word Fixed Author:{entry['fixed_author']}")
             print(f"Original Content: {entry['original_content']}")
             print(f"Word Fixed Content:{entry['fixed_content']}")
             if entry['original_content'] != entry['fixed_content'] or entry.get('original_author') != entry.get('fixed_author'):
                 print(" ^^^ Changes Applied ^^^")