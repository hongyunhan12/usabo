"""
Chinese Flashcard App - Interactive flashcard application similar to Quizlet
Reads Chinese words from Excel file and displays them as interactive flashcards
"""
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import pandas as pd
import re
from pathlib import Path
from typing import List, Dict
import os

# Initialize FastAPI app
app = FastAPI(title="Chinese Flashcard App", version="1.0.0")

# Templates directory - use absolute path
TEMPLATE_DIR = Path(__file__).parent / "templates"
if not TEMPLATE_DIR.exists():
    raise FileNotFoundError(f"Templates directory not found at: {TEMPLATE_DIR}")
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))

# Path to Excel file - supports environment variable for deployment
# Priority: 1. Environment variable, 2. Default path, 3. Current directory
EXCEL_FILE_ENV = os.getenv("EXCEL_FILE_PATH")
DEFAULT_EXCEL_PATH = Path(r"C:\Users\nieli\Documents\Flashcard\Chinese_words_list.xlsx")
CURRENT_DIR_EXCEL = Path("Chinese_words_list.xlsx")

# Determine which Excel file to use
if EXCEL_FILE_ENV and Path(EXCEL_FILE_ENV).exists():
    EXCEL_FILE_PATH = Path(EXCEL_FILE_ENV)
elif DEFAULT_EXCEL_PATH.exists():
    EXCEL_FILE_PATH = DEFAULT_EXCEL_PATH
elif CURRENT_DIR_EXCEL.exists():
    EXCEL_FILE_PATH = CURRENT_DIR_EXCEL
else:
    EXCEL_FILE_PATH = DEFAULT_EXCEL_PATH  # Will show error when loading

# Cache for flashcards data
flashcards_cache: List[Dict] = []


def parse_sound_meaning(sound_meaning: str) -> tuple:
    """
    Parse the sound_meaning column to extract pronunciation and meaning.
    
    Format: "pronunciation      meaning"
    Examples:
    - "de/di2/di4      (possessive particle)/of, really and truly, aim/clear"
    - "yi1     one/1/single/a(n)"
    - "bu4/bu2 (negative prefix)/not/no"
    - "shi4    is/are/am/yes/to be"
    
    Returns: (pronunciation, meaning)
    """
    if pd.isna(sound_meaning) or not sound_meaning:
        return "", ""
    
    sound_meaning = str(sound_meaning).strip()
    
    # Method 1: Split by multiple spaces (2 or more) or tabs
    # This handles cases like "yi1     one/1/single/a(n)"
    parts = re.split(r'\s{2,}|\t+', sound_meaning, maxsplit=1)
    
    if len(parts) == 2:
        pronunciation = parts[0].strip()
        meaning = parts[1].strip()
        return pronunciation, meaning
    
    # Method 2: Look for pattern where pinyin ends (contains numbers or slashes)
    # and meaning starts (often with parentheses or after significant whitespace)
    # Pattern: pinyin (ends with number or /) followed by spaces and meaning
    match = re.match(r'^([^\s()]+(?:[/\d]+)?(?:\s+[^\s()]+(?:[/\d]+)?)*)\s+([(].*|.+)', sound_meaning)
    if match:
        pronunciation = match.group(1).strip()
        meaning = match.group(2).strip()
        return pronunciation, meaning
    
    # Method 3: Split by first occurrence of significant whitespace
    # Find the first instance of 3+ spaces or a tab
    match = re.match(r'^(.+?)(\s{3,}|\t+)(.+)', sound_meaning)
    if match:
        pronunciation = match.group(1).strip()
        meaning = match.group(3).strip()
        return pronunciation, meaning
    
    # Method 4: Fallback - try to split by single space and take first part as pronunciation
    # This handles cases like "bu4/bu2 (negative prefix)/not/no" where there's only one space
    words = sound_meaning.split(None, 1)  # Split on whitespace, max 1 split
    if len(words) == 2:
        pronunciation = words[0]
        meaning = words[1]
    else:
        # Last resort: return everything as pronunciation
        pronunciation = sound_meaning
        meaning = ""
    
    return pronunciation, meaning


def load_flashcards() -> List[Dict]:
    """Load flashcards from Excel file and parse the data"""
    global flashcards_cache
    
    if flashcards_cache:
        return flashcards_cache
    
    try:
        # Read Excel file
        df = pd.read_excel(EXCEL_FILE_PATH)
        
        # Check if required columns exist
        if 'word' not in df.columns or 'sound_meaning' not in df.columns:
            raise ValueError("Excel file must contain 'word' and 'sound_meaning' columns")
        
        flashcards = []
        
        for idx, row in df.iterrows():
            word = str(row['word']).strip()
            sound_meaning = row['sound_meaning']
            
            pronunciation, meaning = parse_sound_meaning(sound_meaning)
            
            flashcards.append({
                'id': idx + 1,
                'word': word,
                'pronunciation': pronunciation,
                'meaning': meaning
            })
        
        flashcards_cache = flashcards
        return flashcards
    
    except FileNotFoundError:
        raise FileNotFoundError(f"Excel file not found at: {EXCEL_FILE_PATH}")
    except Exception as e:
        raise Exception(f"Error loading flashcards: {str(e)}")


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Serve the main flashcard page"""
    return templates.TemplateResponse("flashcard.html", {"request": request})


@app.get("/api/flashcards")
async def get_flashcards(block: int = None):
    """API endpoint to get all flashcards or filtered by block
    
    Args:
        block: Optional block number (1-based). Each block contains 100 words.
              If None, returns all flashcards.
    """
    try:
        flashcards = load_flashcards()
        total = len(flashcards)
        
        # Calculate total number of blocks
        total_blocks = (total + 99) // 100  # Ceiling division
        
        # Filter by block if specified
        if block is not None:
            start_idx = (block - 1) * 100
            end_idx = min(start_idx + 100, total)
            filtered_flashcards = flashcards[start_idx:end_idx]
            return {
                "flashcards": filtered_flashcards,
                "total": len(filtered_flashcards),
                "block": block,
                "total_blocks": total_blocks,
                "block_range": f"{start_idx + 1}-{end_idx}"
            }
        
        return {
            "flashcards": flashcards,
            "total": total,
            "total_blocks": total_blocks
        }
    except Exception as e:
        return {"error": str(e), "flashcards": [], "total": 0}


@app.get("/api/flashcard/{card_id}")
async def get_flashcard(card_id: int):
    """API endpoint to get a specific flashcard by ID"""
    flashcards = load_flashcards()
    
    if card_id < 1 or card_id > len(flashcards):
        return {"error": "Flashcard not found"}
    
    return flashcards[card_id - 1]


if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("Starting Chinese Flashcard App...")
    print(f"Excel file path: {EXCEL_FILE_PATH}")
    print(f"Excel file exists: {EXCEL_FILE_PATH.exists()}")
    print(f"Template directory: {TEMPLATE_DIR}")
    print(f"Template directory exists: {TEMPLATE_DIR.exists()}")
    print("=" * 60)
    # Try port 8001 first, if busy try 8002
    import socket
    port = 8001
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', port))
    sock.close()
    if result == 0:
        print(f"Port {port} is busy, trying port 8002...")
        port = 8002
    
    # Use PORT environment variable if available (for cloud deployment)
    port = int(os.getenv("PORT", port))
    
    print(f"Server starting at: http://localhost:{port}")
    print("Press Ctrl+C to stop the server")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")

