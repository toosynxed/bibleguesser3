from flask import Flask, render_template, jsonify, request, send_from_directory
import os
import re, random
import json

app = Flask(__name__,
            template_folder='.',  # Use current directory for templates
            static_folder='.')    # Use current directory for static files

# Route for the home page
@app.route('/')
def home():
    return send_from_directory('.', 'home.html')

@app.route('/bibleguesser.html')
def sst55x():
    return send_from_directory('.', 'bibleguesser.html')

@app.route('/marathon.html')
def marathon_page():
    return send_from_directory('.', 'marathon.html')

@app.route('/result.html')
def result_page():
    return send_from_directory('.', 'result.html')

 # Route to serve CSS files
@app.route('/style.css')
def css():
    return send_from_directory('.', 'style.css')

@app.route('/result.css')
def result_css():
    return send_from_directory('.', 'result.css')

@app.route('/result.js')
def result_js():
    return send_from_directory('.', 'result.js')

# Health check endpoint
@app.route('/api/health')
def health_check():
    return jsonify({
        "status": "healthy",
        "message": "Flask backend is running!"
    })

# Load the Bible from the JSON file
with open('bible.json', 'r') as f:
    bible_data = json.load(f)

# --- Share Code Obfuscation Logic ---

# Using generous upper bounds for chapters in a book and verses in a chapter
MAX_CHAPTERS = 200
MAX_VERSES = 250
ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyz"

def encode_reference(book_idx, chapter_idx, verse_idx):
    """Encodes numeric bible reference into a single obfuscated string."""
    # Combine indices into one unique integer
    unique_id = (book_idx * MAX_CHAPTERS * MAX_VERSES) + (chapter_idx * MAX_VERSES) + verse_idx
    
    # Convert the integer to a base36 string for obfuscation
    if unique_id == 0:
        return ALPHABET[0]
    
    base36_str = ""
    while unique_id > 0:
        unique_id, remainder = divmod(unique_id, 36)
        base36_str = ALPHABET[remainder] + base36_str
    return base36_str

def decode_reference(share_code):
    """Decodes an obfuscated share code back into (book, chapter, verse) indices."""
    # Convert base36 string back to an integer
    unique_id = int(share_code, 36)
    
    verse_idx = unique_id % MAX_VERSES
    temp = unique_id // MAX_VERSES
    chapter_idx = temp % MAX_CHAPTERS
    book_idx = temp // MAX_CHAPTERS
    return book_idx, chapter_idx, verse_idx

@app.route('/bibleguesser.js')
def bible_guesser_js():
    return send_from_directory('.', 'bibleguesser.js')

@app.route('/api/random-verse-with-context')
def random_verse():
    import random
    context_size = int(request.args.get('context', 0))

    # Find a book and chapter that are large enough for the selected context size
    suitable_chapter_found = False
    while not suitable_chapter_found:
        book_index = random.randint(0, len(bible_data) - 1)
        random_book = bible_data[book_index]

        if not random_book['chapters']: continue # Skip books with no chapters

        chapter_index = random.randint(0, len(random_book['chapters']) - 1)
        random_chapter = random_book['chapters'][chapter_index]

        # A suitable chapter must have at least (context_size * 2) + 1 verses
        if len(random_chapter['verses']) > context_size * 2:
            suitable_chapter_found = True

    # Select a random verse, ensuring there's enough context on both sides
    min_index = context_size
    # Ensure max_index is not less than min_index
    max_index = max(min_index, len(random_chapter['verses']) - 1 - context_size)
    verse_index = random.randint(min_index, max_index) # This is the index within the chapter's verses list
    
    target_verse_obj = random_chapter['verses'][verse_index]

    # Get surrounding verses for context
    start_index = max(0, verse_index - context_size)
    end_index = min(len(random_chapter['verses']), verse_index + context_size + 1)
    context_verses = random_chapter['verses'][start_index:end_index]

    # Generate a shareable code: book_index-chapter_index-verse_index
    share_code = encode_reference(book_index, chapter_index, verse_index)

    # Prepare the response
    response_data = {
        "reference": f"{random_book['book']} {random_chapter['chapter']}:{target_verse_obj['verse']}",
        "target_verse_index_in_context": verse_index - start_index,
        "context_verses": context_verses,
        "share_code": share_code
    }

    return jsonify(response_data)

@app.route('/api/verse-from-code')
def verse_from_code():
    share_code = request.args.get('code')
    context_size = int(request.args.get('context', 0))

    try:
        book_idx, chapter_idx, verse_idx = decode_reference(share_code)

        book = bible_data[book_idx]
        chapter = book['chapters'][chapter_idx]
        target_verse_obj = chapter['verses'][verse_idx]

        # Get surrounding verses for context
        start_index = max(0, verse_idx - context_size)
        end_index = min(len(chapter['verses']), verse_idx + context_size + 1)
        context_verses = chapter['verses'][start_index:end_index]

        response_data = {
            "reference": f"{book['book']} {chapter['chapter']}:{target_verse_obj['verse']}",
            "target_verse_index_in_context": verse_idx - start_index,
            "context_verses": context_verses,
            "share_code": share_code
        }
        return jsonify(response_data)

    except (ValueError, IndexError, TypeError):
        return jsonify({
            "error": "Invalid or expired share code.",
            "message": "The provided code is not valid. Please try a new one or get a random verse."
        }), 400

def get_single_random_verse(context_size):
    """Helper function to get a single random verse object."""
    suitable_chapter_found = False
    while not suitable_chapter_found:
        book_index = random.randint(0, len(bible_data) - 1)
        random_book = bible_data[book_index]

        if not random_book['chapters']: continue

        chapter_index = random.randint(0, len(random_book['chapters']) - 1)
        random_chapter = random_book['chapters'][chapter_index]

        if len(random_chapter['verses']) > context_size * 2:
            suitable_chapter_found = True

    min_index = context_size
    max_index = max(min_index, len(random_chapter['verses']) - 1 - context_size)
    verse_index = random.randint(min_index, max_index)
    
    target_verse_obj = random_chapter['verses'][verse_index]

    start_index = max(0, verse_index - context_size)
    end_index = min(len(random_chapter['verses']), verse_index + context_size + 1)
    context_verses = random_chapter['verses'][start_index:end_index]

    share_code = encode_reference(book_index, chapter_index, verse_index)

    return {
        "reference": f"{random_book['book']} {random_chapter['chapter']}:{target_verse_obj['verse']}",
        "target_verse_index_in_context": verse_index - start_index,
        "context_verses": context_verses,
        "share_code": share_code
    }

@app.route('/api/marathon-verses')
def marathon_verses():
    """Generates a set of 5 random verses for Marathon Mode."""
    verses = [get_single_random_verse(context_size=2) for _ in range(5)]
    # Combine individual share codes into one marathon code
    marathon_share_code = ".".join([v['share_code'] for v in verses])
    return jsonify({
        "verses": verses,
        "marathon_share_code": marathon_share_code
    })

@app.route('/api/marathon-from-code')
def marathon_from_code():
    """Retrieves a set of 5 verses from a marathon share code."""
    marathon_code = request.args.get('code')
    if not marathon_code:
        return jsonify({"error": "No code provided."}), 400
    
    individual_codes = marathon_code.split('.')
    if len(individual_codes) != 5:
        return jsonify({"error": "Invalid marathon code."}), 400

    # This part is left for you to implement if needed, or handle on the client-side.
    # For simplicity, the client will fetch each verse individually using its code.
    return jsonify({"message": "Endpoint for marathon code validation."})


@app.route('/api/check-guess', methods=['POST'])
def check_guess():
    data = request.get_json()
    user_guess_str = data.get('guess', '').strip()
    correct_text = data.get('verse', {}).get('text', '')
    correct_reference_str = data.get('verse', {}).get('reference', '').strip()

    # --- Helper Functions ---

    def find_book(book_name):
        """Finds a book in bible_data, ignoring case and spaces."""
        book_name_norm = book_name.lower().replace(" ", "")
        for book in bible_data:
            if book['book'].lower().replace(" ", "") == book_name_norm:
                return book
        return None

    def find_chapter(book_obj, chapter_num):
        """Finds a chapter within a book object."""
        if not book_obj:
            return None
        for chapter in book_obj['chapters']:
            if chapter['chapter'] == chapter_num:
                return chapter
        return None

    def find_verse(chapter_obj, verse_num):
        """Finds a verse within a chapter object."""
        if not chapter_obj:
            return None
        for verse in chapter_obj['verses']:
            if verse['verse'] == verse_num:
                return verse
        return None

    def get_proximity_score(user_num, correct_num, max_items):
        """Calculates a proximity score from 0-100 for chapter/verse numbers."""
        # Avoid division by zero for single-verse chapters
        if max_items <= 1:
            return 100 if user_num == correct_num else 0
        distance = abs(user_num - correct_num)
        return max(0, 100 - int((distance / (max_items -1)) * 100))

    def parse_reference(ref_str):
        """Parses a reference string into (book, chapter, verse). Returns None on failure."""
        # Regex to handle book names with or without a leading number (e.g., "1 Samuel", "Genesis")
        match = re.match(r'^(\d?\s?[a-zA-Z\s]+?)\s+(\d+):(\d+)$', ref_str.strip())
        if not match:
            return None
        
        book, chapter, verse = match.groups()
        return book.strip(), int(chapter), int(verse)

    # --- Main Logic ---

    correct_parts = parse_reference(correct_reference_str)
    user_parts = parse_reference(user_guess_str)

    if not user_parts:
        return jsonify({
            "score": 0,
            "stars": {"book": False, "chapter": False, "verse": False},
            "message": "Invalid format. Please use 'Book Chapter:Verse'.",
            "correct_answer": correct_reference_str,
            "correct_text": correct_text
        })

    user_book_name, user_chapter_num, user_verse_num = user_parts
    correct_book_name, correct_chapter_num, correct_verse_num = correct_parts

    stars = {"book": False, "chapter": False, "verse": False}
    score = 0
    message = ""

    # --- Component-based Checking & Scoring ---

    # 1. Book Check
    correct_book_obj = find_book(correct_book_name)
    user_book_obj = find_book(user_book_name)

    if not user_book_obj:
        message = f"The book '{user_book_name}' was not found."
    elif user_book_obj['book'] == correct_book_obj['book']: # Correct Book
        stars["book"] = True
        score += 34  # Award points for correct book

        # Nested Check for Chapter (since book is correct)
        correct_chapter_obj = find_chapter(correct_book_obj, correct_chapter_num)
        user_chapter_obj = find_chapter(user_book_obj, user_chapter_num)

        if not user_chapter_obj:
            message = f"Chapter {user_chapter_num} does not exist in the book of {user_book_name}."
            # Give proximity score for chapter number since book was correct
            score += get_proximity_score(user_chapter_num, correct_chapter_num, len(correct_book_obj['chapters'])) * 0.33
        elif user_chapter_num == correct_chapter_num: # Correct Chapter
            stars["chapter"] = True # Chapter is correct, so award the star
            score += 33  # Award points for correct chapter

            # Nested Check for Verse (since book and chapter are correct)
            user_verse_obj = find_verse(user_chapter_obj, user_verse_num)
            distance = abs(user_verse_num - correct_verse_num) # Calculate distance for scoring
            if not user_verse_obj:
                message = f"Verse {user_verse_num} does not exist in {user_book_name} {user_chapter_num}."
                # Give partial points for verse proximity, capped at 33
                score += max(0, 33 - distance)
            elif user_verse_num == correct_verse_num: # Correct Verse
                stars["verse"] = True
                score += 33  # Award points for correct verse
                message = "Perfect guess!"
            else: # Correct book and chapter, but wrong verse
                message = "You have the right book and chapter, but the verse is off."
                score += max(0, 33 - distance)
        else: # Correct book, but wrong chapter
            message = "You have the right book, but the chapter is off."
            # Give proximity score for chapter number
            score += get_proximity_score(user_chapter_num, correct_chapter_num, len(correct_book_obj['chapters'])) * 0.33
    else: # Wrong book
        message = "Your guessed book is incorrect."
        # If the book is wrong, no stars can be awarded for chapter or verse,
        # so we don't need to check them here. The stars dictionary is already
        # initialized to all False.

    # Final score is an integer
    score = int(round(score))

    return jsonify({
        "score": score,
        "stars": stars,
        "message": message,
        "correct_answer": correct_reference_str,
        "correct_text": correct_text
    })

if __name__ == '__main__':
    print("Starting Flask server...")
    print("Available routes:")
    print("- http://localhost:5000/ (Home page)")
    print("- http://localhost:5000/bibleguesser.html (Bible Guesser)")
    print("- http://localhost:5002/api/health (Health check)")
    app.run(debug=True, port=5002)
