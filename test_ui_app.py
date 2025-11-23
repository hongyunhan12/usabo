"""
Interactive Test UI Application for PDF-based tests
"""
import os
import re
import json
from pathlib import Path
from typing import List, Dict, Optional
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import pdfplumber
try:
    import pandas as pd
    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False
    print("Warning: pandas not installed. Excel file support disabled. Install with: pip install pandas openpyxl")

app = FastAPI(title="Interactive Test UI")

# Directories
TEST_DIR = Path(r"C:\Users\nieli\Documents\USABO\Test")
KEY_DIR = Path(r"C:\Users\nieli\Documents\USABO\Key")
ANSWER_DIR = Path(r"C:\Users\nieli\Documents\USABO\UserAnswer")

# Ensure directories exist
ANSWER_DIR.mkdir(parents=True, exist_ok=True)

# Templates - use absolute path to avoid issues
import os
TEMPLATE_DIR = Path(__file__).parent / "templates"
if not TEMPLATE_DIR.exists():
    raise FileNotFoundError(f"Templates directory not found at: {TEMPLATE_DIR}")
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))


class Question:
    """Represents a question from the PDF"""
    def __init__(self, number: int, text: str, question_type: str, choices: Optional[List[str]] = None):
        self.number = number
        self.text = text
        self.type = question_type  # "multiple_choice" or "short_answer"
        self.choices = choices or []


def clean_text(text: str) -> str:
    """Remove unwanted text like headers, footers, page numbers"""
    if not text:
        return ""
    # Remove common unwanted patterns
    unwanted_patterns = [
        r'USABO\s+Open\s+Exam',
        r'Answer\s+Key',
        r'Page\s+\d+',
        r'^\d+\s*$',  # Standalone page numbers
        r'^Page\s+\d+',
    ]
    
    for pattern in unwanted_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    return text.strip()


def extract_questions_from_pdf(pdf_path: Path) -> List[Question]:
    """
    Extract questions from PDF file with improved filtering
    Handles multiple formats:
    - "3. Question text [ ] A. choice [ ] B. choice..." (inline)
    - "3. Question text\nA. choice\nB. choice..." (separate lines)
    """
    questions = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            full_text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    full_text += page_text + "\n"
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading PDF: {str(e)}")
    
    if not full_text.strip():
        raise HTTPException(status_code=500, detail="PDF appears to be empty or unreadable")
    
    # Clean the full text
    full_text = clean_text(full_text)
    
    # Split into lines for processing
    lines = full_text.split('\n')
    filtered_lines = []
    for line in lines:
        line = line.strip()
        if not line:
            filtered_lines.append("")  # Keep empty lines as separators
            continue
        # Skip header/footer lines
        if re.match(r'^(USABO|Answer Key|Page \d+)$', line, re.IGNORECASE):
            continue
        # Skip lines that are just page numbers
        if re.match(r'^\d+$', line):
            continue
        filtered_lines.append(line)
    
    # Pattern to identify question numbers - MUST start at beginning of line
    question_pattern = re.compile(r'^(\d+)\.\s*(.+)$')
    # Pattern to identify choices: "[ ] A." or "A." format
    choice_pattern_with_brackets = re.compile(r'^\[\s*\]\s*([A-E])\.\s*(.+)$')
    choice_pattern_simple = re.compile(r'^([A-E])[\)\.]\s*(.+)$')
    
    i = 0
    while i < len(filtered_lines):
        line = filtered_lines[i]
        
            # Check if this is a question number
        question_match = question_pattern.match(line)
        if question_match:
            question_num = int(question_match.group(1))
            # Start with the question text from the first line
            question_text_parts = [question_match.group(2).strip()]
            
            choices = []
            has_inline_choices = False
            
            # Check for inline choices with [ ] markers on the same line
            if '[]' in line or re.search(r'\[\s*\]\s*[A-E]\.', line):
                inline_choice_pattern = r'\[\s*\]\s*([A-E])\.\s*([^\[\]]+?)(?=\s*\[\s*\]\s*[A-E]\.|$)'
                inline_matches = re.finditer(inline_choice_pattern, line)
                for m in inline_matches:
                    choice_text = m.group(2).strip()
                    choice_text = clean_text(choice_text)
                    if choice_text:
                        choices.append(choice_text)
                has_inline_choices = True
                # Remove choices from question text
                question_text_parts[0] = re.sub(r'\[\s*\]\s*[A-E]\.[^\[\]]+', '', question_text_parts[0]).strip()
            
            # Look ahead to collect all question text lines before first choice
            if not has_inline_choices:
                j = i + 1
                found_first_choice = False
                consecutive_non_choice = 0
                max_consecutive_non_choice = 3
                
                while j < len(filtered_lines) and j < i + 30:  # Look ahead up to 30 lines
                    next_line = filtered_lines[j]
                    
                    # CRITICAL: Stop immediately if we hit another question number
                    if question_pattern.match(next_line):
                            break
                    
                    # Check if this line is a choice - try [ ] A. format first (most common)
                    choice_match = choice_pattern_with_brackets.match(next_line)
                    if not choice_match:
                        choice_match = choice_pattern_simple.match(next_line)
                    
                    if choice_match:
                        # Found first choice - stop collecting question text, start collecting choices
                        if not found_first_choice:
                            found_first_choice = True
                        
                        choice_letter = choice_match.group(1)
                        choice_text = choice_match.group(2).strip()
                        choice_text = clean_text(choice_text)
                        
                        if choice_text and len(choice_text) < 500:
                            choices.append(choice_text)
                            consecutive_non_choice = 0  # Reset counter
                    else:
                        # Not a choice line
                        if found_first_choice:
                            # We've already found at least one choice - collecting more choices
                            if not next_line.strip():
                                # Empty line - continue collecting choices (allow empty lines between choices)
                                consecutive_non_choice += 1
                            else:
                                # Non-empty, non-choice line - might be end of choices
                                consecutive_non_choice += 1
                                if consecutive_non_choice > max_consecutive_non_choice:
                                    break
                        else:
                            # Haven't found first choice yet - this is part of question text
                            # Collect ALL lines until we find the first [ ] A. choice
                            if next_line.strip():  # Only add non-empty lines
                                question_text_parts.append(next_line.strip())
                    
                    j += 1
            
            # Join all question text parts with newlines (preserve line breaks for readability)
            # Then replace multiple newlines with single space, but keep structure
            question_text = "\n".join(question_text_parts)
            question_text = clean_text(question_text)
            question_text = re.sub(r'\[\s*\]', '', question_text).strip()
            # Replace multiple whitespace/newlines with single space for cleaner display
            question_text = re.sub(r'\s+', ' ', question_text).strip()
            
            # Create question object
            if len(choices) >= 2:
                q = Question(question_num, question_text, "multiple_choice", choices)
            else:
                q = Question(question_num, question_text, "short_answer")
            
            questions.append(q)
            i += 1
        else:
            i += 1
    
    # Final cleaning
    for q in questions:
        q.text = clean_text(q.text)
        q.text = re.sub(r'\[\s*\]', '', q.text).strip()
        q.choices = [clean_text(c) for c in q.choices if clean_text(c)]
    
    # Remove duplicates (keep first occurrence) and sort by question number
    seen_numbers = {}
    unique_questions = []
    for q in questions:
        if q.number not in seen_numbers:
            seen_numbers[q.number] = True
            unique_questions.append(q)
    
    unique_questions.sort(key=lambda x: x.number)
    
    return unique_questions


def extract_answer_key_from_pdf(key_path: Path) -> Dict[int, str]:
    """
    Extract answer key from PDF file
    Tries multiple methods: yellow highlights, filled checkboxes, text patterns
    Returns a dictionary mapping question number to correct answer
    """
    answer_key = {}
    
    try:
        with pdfplumber.open(key_path) as pdf:
            # Extract text from all pages
            full_text = ""
            page_texts = []
            for page_num, page in enumerate(pdf.pages, 1):
                page_text = page.extract_text()
                if page_text:
                    full_text += page_text + "\n"
                    page_texts.append({
                        'page_num': page_num,
                        'text': page_text,
                        'chars': page.chars,
                        'page': page
                    })
            
            if not full_text.strip():
                print("Warning: PDF appears to be empty or unreadable")
                return answer_key
            
            full_text = clean_text(full_text)
            lines = full_text.split('\n')
            
            # METHOD 1: Try yellow highlight detection (if highlights exist)
            yellow_answers = {}
            for page_data in page_texts:
                page = page_data['page']
                chars = page_data['chars']
                rects = page.rects if hasattr(page, 'rects') else []
                
                # Find yellow rectangles
                yellow_rects = []
                for rect in rects:
                    color = rect.get('non_stroking_color', None)
                    if color and isinstance(color, tuple) and len(color) == 3:
                        r, g, b = color
                        if r > 0.8 and g > 0.8 and b < 0.3:  # Yellow
                            yellow_rects.append(rect)
                
                # Process yellow highlights (same logic as before)
                if yellow_rects:
                    # Build question positions map
                    question_positions = {}
                    for i, char in enumerate(chars):
                        if char['text'].isdigit() and i + 1 < len(chars):
                            if chars[i + 1]['text'] == '.':
                                question_digits = []
                                for j in range(max(0, i - 2), i + 1):
                                    if chars[j]['text'].isdigit():
                                        question_digits.append(chars[j]['text'])
                                if question_digits:
                                    q_num = int(''.join(question_digits))
                                    if q_num not in question_positions:
                                        question_positions[q_num] = {'y': char['top'], 'x': char['x0']}
                    
                    # Map yellow highlights to questions (simplified version)
                    for yellow_rect in yellow_rects:
                        rect_center_y = (yellow_rect['y0'] + yellow_rect['y1']) / 2
                        rect_x0 = yellow_rect['x0']
                        
                        # Find overlapping text
                        overlapping_chars = [c for c in chars if 
                                           (c['x0'] < yellow_rect['x1'] and c['x1'] > yellow_rect['x0'] and
                                            c['y0'] < yellow_rect['y1'] and c['y1'] > yellow_rect['y0'])]
                        
                        if overlapping_chars:
                            highlighted_text = ''.join([c['text'] for c in sorted(overlapping_chars, key=lambda x: (x['top'], x['x0']))]).strip()
                            
                            # Find choice letter nearby
                            nearby_chars = [c for c in chars if abs(c['x0'] - rect_x0) < 50 and abs((c['y0'] + c['y1']) / 2 - rect_center_y) < 20]
                            nearby_text = ''.join([c['text'] for c in sorted(nearby_chars, key=lambda x: (x['top'], x['x0']))])
                            choice_match = re.search(r'\b([A-E])\.', nearby_text)
                            
                            if choice_match:
                                answer_letter = choice_match.group(1).upper()
                                # Find nearest question above
                                best_q = None
                                min_dist = float('inf')
                                for q_num, q_pos in question_positions.items():
                                    if q_pos['y'] > rect_center_y:
                                        dist = q_pos['y'] - rect_center_y
                                        x_diff = abs(q_pos['x'] - rect_x0)
                                        if x_diff < 200 and dist < 200:
                                            weighted = dist + (x_diff * 0.5)
                                            if weighted < min_dist:
                                                min_dist = weighted
                                                best_q = q_num
                                
                                if best_q and answer_letter in ['A', 'B', 'C', 'D', 'E']:
                                    yellow_answers[best_q] = answer_letter
            
            # METHOD 2: Text-based extraction (primary method for non-highlighted keys)
            # Pattern 1: Filled checkboxes [X] A. or [✓] A. or [☑] A.
            for i, line in enumerate(lines):
                line = line.strip()
                if not line:
                    continue
                
                # Look for filled checkbox pattern: [X] A. or [✓] A. or [☑] A.
                checkbox_pattern = r'\[[Xx✓☑]\s*\]\s*([A-E])\.'
                match = re.search(checkbox_pattern, line)
                if match:
                    answer_letter = match.group(1).upper()
                    # Look backwards for question number
                    for j in range(max(0, i - 15), i + 1):
                        q_match = re.search(r'^(\d+)\.', lines[j])
                        if q_match:
                            q_num = int(q_match.group(1))
                            if q_num not in answer_key:
                                answer_key[q_num] = answer_letter
                            break
            
            # Pattern 2: Simple answer list format: "1. A 2. B 3. C" or "1. A\n2. B\n3. C"
            # Check for compact format on single line
            compact_pattern = r'(\d+)[\.\)]\s*([A-E])(?:\s+(\d+)[\.\)]\s*([A-E]))*'
            for line in lines:
                line = line.strip()
                if not line or len(line) > 200:  # Skip very long lines
                    continue
                
                # Find all matches in this line
                matches = re.findall(r'(\d+)[\.\)]\s*([A-E])', line, re.IGNORECASE)
                for match in matches:
                    q_num = int(match[0])
                    answer = match[1].upper()
                    if answer in ['A', 'B', 'C', 'D', 'E']:
                        if q_num not in answer_key:
                            answer_key[q_num] = answer
            
            # Pattern 3: Standalone answer lines: "3. B" or "3) B" or "3 B" or "1 C"
            # This is the most common format: number followed by space and letter
            standalone_patterns = [
                r'^(\d+)[\.\)]\s*([A-E])[\.\)]?\s*$',  # "3. B" or "3) B"
                r'^(\d+)\s+([A-E])\s*$',                # "3 B" or "1 C" (one or more spaces)
                r'^(\d+)\s([A-E])\s*$',                 # "3 B" or "1 C" (single space)
            ]
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Skip header lines
                if line.lower() in ['questions answers', 'answers', 'answer key', 'key']:
                    continue
                
                # Skip lines that look like questions (too long or have question text)
                # But allow short lines that match our pattern
                if len(line) > 50 and not re.match(r'^\d+[\.\)\s]+[A-E]', line, re.IGNORECASE):
                    continue
                
                for pattern in standalone_patterns:
                    match = re.match(pattern, line, re.IGNORECASE)
                    if match:
                        q_num = int(match.group(1))
                        answer = match.group(2).upper()
                        if answer in ['A', 'B', 'C', 'D', 'E']:
                            if q_num not in answer_key:
                                answer_key[q_num] = answer
                            break
            
            # Pattern 4: Answer key format: "Question 3: B" or "3. Answer: B"
            answer_label_patterns = [
                r'(\d+)[\.\)]\s*Answer[:\s]+([A-E])',
                r'Question\s+(\d+)[:\s]+([A-E])',
                r'Q\s*(\d+)[:\s]+([A-E])',
            ]
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                for pattern in answer_label_patterns:
                    match = re.search(pattern, line, re.IGNORECASE)
                    if match:
                        q_num = int(match.group(1))
                        answer = match.group(2).upper()
                        if answer in ['A', 'B', 'C', 'D', 'E']:
                            if q_num not in answer_key:
                                answer_key[q_num] = answer
                            break
            
            # Pattern 5: Look for answers in question context (if key file has full questions)
            # Find questions with filled checkboxes in the same context
            for i, line in enumerate(lines):
                q_match = re.search(r'^(\d+)\.', line)
                if q_match:
                    q_num = int(q_match.group(1))
                    # Look ahead in next 10 lines for filled checkbox
                    for j in range(i + 1, min(i + 11, len(lines))):
                        next_line = lines[j].strip()
                        # Check if this is a new question (stop searching)
                        if re.match(r'^\d+\.', next_line):
                            break
                        # Look for filled checkbox
                        checkbox_match = re.search(r'\[[Xx✓☑]\s*\]\s*([A-E])\.', next_line)
                        if checkbox_match:
                            answer_letter = checkbox_match.group(1).upper()
                            if q_num not in answer_key:
                                answer_key[q_num] = answer_letter
                            break
            
            # Merge yellow highlight results (they take precedence if found)
            answer_key.update(yellow_answers)
            
    except Exception as e:
        print(f"Warning: Error reading key PDF: {str(e)}")
        import traceback
        traceback.print_exc()
        return answer_key
    
    extraction_method = "yellow highlights" if yellow_answers else "text patterns"
    print(f"Extracted {len(answer_key)} answers from key file using {extraction_method}")
    if answer_key:
        sample = dict(list(answer_key.items())[:10])
        print(f"Sample answers: {sample}")
    
    return answer_key


def extract_answer_key_from_excel(excel_path: Path) -> Dict[int, str]:
    """
    Extract answer key from Excel file
    Expected format: Columns named "Questions" and "Answers" (or similar)
    Returns a dictionary mapping question numbers to answer letters (A, B, C, D, E)
    """
    answer_key = {}
    
    if not EXCEL_AVAILABLE:
        print("Error: pandas not installed. Cannot read Excel files.")
        return answer_key
    
    if not excel_path.exists():
        print(f"Error: Excel file not found: {excel_path}")
        return answer_key
    
    try:
        # Read Excel file
        df = pd.read_excel(excel_path)
        
        print(f"Excel file loaded: {excel_path.name}")
        print(f"  Shape: {df.shape}")
        print(f"  Columns: {list(df.columns)}")
        
        # Find question and answer columns (case-insensitive, flexible naming)
        question_col = None
        answer_col = None
        
        # Try to find columns by name (case-insensitive)
        for col in df.columns:
            col_lower = str(col).lower().strip()
            if col_lower in ['question', 'questions', 'q', 'q#', 'question #', 'question#', 'num', 'number', '#']:
                question_col = col
            elif col_lower in ['answer', 'answers', 'a', 'ans', 'key', 'correct', 'correct answer', 'correct_answer']:
                answer_col = col
        
        # If not found by name, try by position (first column = questions, second = answers)
        if question_col is None or answer_col is None:
            if len(df.columns) >= 2:
                question_col = df.columns[0]
                answer_col = df.columns[1]
                print(f"  Using first two columns: '{question_col}' and '{answer_col}'")
            else:
                print(f"  Error: Need at least 2 columns, found {len(df.columns)}")
                return answer_key
        
        print(f"  Using columns: Question='{question_col}', Answer='{answer_col}'")
        
        # Extract answers
        for idx, row in df.iterrows():
            try:
                # Get question number
                q_val = row[question_col]
                if pd.isna(q_val):
                    continue
                
                # Convert to int (handle float like 1.0 -> 1)
                if isinstance(q_val, float):
                    q_num = int(q_val)
                elif isinstance(q_val, str):
                    # Extract number from string if needed
                    num_match = re.search(r'(\d+)', q_val)
                    if num_match:
                        q_num = int(num_match.group(1))
                    else:
                        continue
                else:
                    q_num = int(q_val)
                
                # Get answer
                ans_val = row[answer_col]
                if pd.isna(ans_val):
                    continue
                
                # Convert to string and extract letter
                ans_str = str(ans_val).strip().upper()
                
                # Extract letter (A, B, C, D, E)
                letter_match = re.search(r'([A-E])', ans_str)
                if letter_match:
                    answer_letter = letter_match.group(1)
                    if answer_letter in ['A', 'B', 'C', 'D', 'E']:
                        answer_key[q_num] = answer_letter
                
            except (ValueError, KeyError, TypeError) as e:
                # Skip rows that can't be parsed
                continue
        
        print(f"Extracted {len(answer_key)} answers from Excel file")
        if answer_key:
            # Show sample from beginning and end to verify all answers
            sample_start = dict(list(answer_key.items())[:10])
            sample_end = dict(list(answer_key.items())[-10:])
            print(f"Sample answers (first 10): {sample_start}")
            print(f"Sample answers (last 10): {sample_end}")
            # Verify we have all expected questions
            if len(answer_key) > 0:
                min_q = min(answer_key.keys())
                max_q = max(answer_key.keys())
                expected_count = max_q - min_q + 1
                if len(answer_key) != expected_count:
                    missing = [i for i in range(min_q, max_q + 1) if i not in answer_key]
                    print(f"  Warning: Missing question numbers: {missing}")
                else:
                    print(f"  Verified: All questions from {min_q} to {max_q} are present ({len(answer_key)} total)")
        
    except Exception as e:
        print(f"Error reading Excel file: {str(e)}")
        import traceback
        traceback.print_exc()
        return answer_key
    
    return answer_key


def save_answer_key_html(key_path: Path, answer_key: Dict[int, str], output_path: Path):
    """
    Save answer key as a clean HTML file
    """
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Answer Key: {key_path.name}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 600px;
            margin: 40px auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            margin-bottom: 10px;
        }}
        .source-file {{
            color: #666;
            margin-bottom: 30px;
            font-size: 14px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        thead {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }}
        th {{
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }}
        td {{
            padding: 10px 12px;
            border-bottom: 1px solid #e9ecef;
        }}
        tbody tr:hover {{
            background: #f8f9fa;
        }}
        .question-num {{
            font-weight: 600;
            color: #667eea;
        }}
        .answer {{
            font-weight: 600;
            color: #28a745;
            font-size: 18px;
        }}
        .stats {{
            margin-top: 20px;
            padding: 15px;
            background: #e7f3ff;
            border-radius: 5px;
            color: #0c5460;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Answer Key</h1>
        <p class="source-file">Source: {key_path.name}</p>
        
        <div class="stats">
            <strong>Total Answers:</strong> {len(answer_key)}
        </div>
        
        <table>
            <thead>
                <tr>
                    <th>Question #</th>
                    <th>Correct Answer</th>
                </tr>
            </thead>
            <tbody>
"""
    
    # Sort by question number
    sorted_answers = sorted(answer_key.items(), key=lambda x: x[0])
    
    for question_num, answer in sorted_answers:
        html_content += f"""
                <tr>
                    <td class="question-num">{question_num}</td>
                    <td class="answer">{answer}</td>
                </tr>
"""
    
    html_content += """
            </tbody>
        </table>
    </div>
</body>
</html>
"""
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"Answer key saved to: {output_path}")
    except Exception as e:
        print(f"Error saving answer key HTML: {str(e)}")


def find_matching_key_file(test_filename: str) -> Optional[Path]:
    """
    Find matching key file for a test file using name similarity
    Tries various naming conventions and uses similarity matching
    """
    from difflib import SequenceMatcher
    
    test_stem = Path(test_filename).stem
    test_stem_lower = test_stem.lower()
    # Extract year prefix (e.g., "2003" from "2003_OpenExam")
    year_match = re.match(r'^(\d{4})', test_stem)
    test_year = year_match.group(1) if year_match else None
    # Remove common suffixes that might differ
    test_base = test_stem_lower.replace('_test', '').replace('_exam', '').replace('_openexam', '').replace('openexam', '')
    
    if not KEY_DIR.exists():
        print(f"ERROR: Key directory does not exist: {KEY_DIR}")
        return None
    
    print(f"Searching for key file matching: {test_filename}")
    print(f"  Test stem: {test_stem}")
    print(f"  Test base: {test_base}")
    
    # Try exact match patterns first (case-insensitive)
    # Prioritize Excel files over PDF files
    patterns = []
    
    # Excel file patterns (preferred)
    if EXCEL_AVAILABLE:
        patterns.extend([
            f"{test_stem}_key.xlsx",
            f"{test_stem}_Key.xlsx",
            f"{test_stem}_KEY.xlsx",
            f"{test_stem}_answerkey.xlsx",
            f"{test_stem}_AnswerKey.xlsx",
            f"{test_stem}_ANSWERKEY.xlsx",
            f"{test_stem}_answer_key.xlsx",
            f"{test_stem}_Answer_Key.xlsx",
            f"{test_stem}_AnserKey.xlsx",  # Handle typo: AnserKey instead of AnswerKey
            f"{test_stem}_AnserKey_Letter.xlsx",
            f"{test_stem}_answerkey_letter.xlsx",
            f"{test_stem}_AnswerKey_Letter.xlsx",
            f"{test_stem}_key.xls",
            f"{test_stem}_AnserKey.xls",
            f"{test_stem}_AnswerKey.xls",
        ])
    
    # PDF file patterns (fallback)
    patterns.extend([
        f"{test_stem}_key.pdf",
        f"{test_stem}_Key.pdf",
        f"{test_stem}_KEY.pdf",
        f"{test_stem}_answerkey.pdf",
        f"{test_stem}_AnswerKey.pdf",
        f"{test_stem}_ANSWERKEY.pdf",
        f"{test_stem}_answer_key.pdf",
        f"{test_stem}_Answer_Key.pdf",
        f"{test_stem}_AnserKey.pdf",  # Handle typo: AnserKey instead of AnswerKey
        f"{test_stem}_AnserKey_Letter.pdf",  # Handle specific format with typo
        f"{test_stem}_answerkey_letter.pdf",
        f"{test_stem}_AnswerKey_Letter.pdf",
        f"key_{test_stem}.pdf",
        f"Key_{test_stem}.pdf",
    ])
    
    # Base patterns (without full stem)
    if EXCEL_AVAILABLE:
        patterns.extend([
            f"{test_base}_key.xlsx",
            f"{test_base}_AnserKey.xlsx",
            f"{test_base}_AnswerKey.xlsx",
        ])
    patterns.extend([
        f"{test_base}_key.pdf",
        f"{test_base}_Key.pdf",
        f"{test_base}_answerkey.pdf",
        f"{test_base}_AnswerKey.pdf",
        f"{test_base}_AnserKey.pdf",  # Handle typo
        f"{test_base}_AnserKey_Letter.pdf",  # Handle specific format with typo
        f"{test_base}_answer_key.pdf",
        f"key_{test_base}.pdf",
    ])
    
    # If we have a year, try year-based patterns
    if test_year:
        if EXCEL_AVAILABLE:
            patterns.extend([
                f"{test_year}_OpenExam_AnserKey.xlsx",
                f"{test_year}_OpenExam_AnswerKey.xlsx",
                f"{test_year}_OpenExam_key.xlsx",
                f"{test_year}_OpenExam_Key.xlsx",
            ])
        patterns.extend([
            f"{test_year}_OpenExam_AnserKey.pdf",
            f"{test_year}_OpenExam_AnswerKey.pdf",
            f"{test_year}_OpenExam_key.pdf",
            f"{test_year}_OpenExam_Key.pdf",
            f"{test_year}_openexam_anserkey.pdf",
            f"{test_year}_openexam_answerkey.pdf",
        ])
    
    # Also try with original case preserved
    if EXCEL_AVAILABLE:
        patterns.extend([
            f"{test_stem}_AnserKey_Letter.xlsx",
            f"{test_stem}_AnswerKey_Letter.xlsx",
        ])
    patterns.extend([
        f"{test_stem}_AnserKey_Letter.pdf",
        f"{test_stem}_AnswerKey_Letter.pdf",
    ])
    
    for pattern in patterns:
        key_file = KEY_DIR / pattern
        if key_file.exists():
            print(f"  [OK] Found exact match: {key_file.name}")
            return key_file
    
    # Try case-insensitive matching - improved to match by year/prefix
    test_stem_normalized = test_stem.replace('_', '').lower()
    # Extract year from test filename for better matching
    test_year_normalized = test_year.lower() if test_year else None
    
    # Search for Excel files first (preferred), then PDF files
    file_extensions = []
    if EXCEL_AVAILABLE:
        file_extensions.extend(['*.xlsx', '*.xls'])
    file_extensions.append('*.pdf')
    
    for ext in file_extensions:
        for key_file in KEY_DIR.glob(ext):
            # Skip temporary Excel files (starting with ~$)
            if key_file.name.startswith('~$'):
                continue
                
            key_stem_normalized = key_file.stem.replace('_', '').lower()
            key_stem_lower = key_file.stem.lower()
            
            # Check if it contains key-related words
            has_key_word = any(word in key_stem_lower for word in ['key', 'answer', 'anser'])
            
            # Match by year if available
            if test_year_normalized and test_year_normalized in key_stem_normalized:
                if has_key_word:
                    print(f"  [OK] Found year-based match: {key_file.name}")
                    return key_file
            
            # Match by stem similarity
            if test_stem_normalized in key_stem_normalized or key_stem_normalized in test_stem_normalized:
                if has_key_word:
                    print(f"  [OK] Found case-insensitive match: {key_file.name}")
                    return key_file
    
    # Try just "key" or "Key" (single key file)
    if EXCEL_AVAILABLE:
        key_file = KEY_DIR / "key.xlsx"
        if key_file.exists():
            return key_file
        key_file = KEY_DIR / "Key.xlsx"
        if key_file.exists():
            return key_file
    
    key_file = KEY_DIR / "key.pdf"
    if key_file.exists():
        return key_file
    
    key_file = KEY_DIR / "Key.pdf"
    if key_file.exists():
        return key_file
    
    # Use similarity matching to find best match
    best_match = None
    best_ratio = 0.0
    
    # Collect all available key files (Excel and PDF)
    available_keys = []
    if EXCEL_AVAILABLE:
        available_keys.extend(KEY_DIR.glob("*.xlsx"))
        available_keys.extend(KEY_DIR.glob("*.xls"))
    available_keys.extend(KEY_DIR.glob("*.pdf"))
    # Filter out temporary Excel files
    available_keys = [k for k in available_keys if not k.name.startswith('~$')]
    
    print(f"  Available key files: {[k.name for k in available_keys]}")
    
    for key_file in available_keys:
        key_stem = key_file.stem
        key_stem_lower = key_stem.lower()
        # Remove common key-related suffixes for comparison (including typo variants)
        key_base = key_stem_lower.replace('_key', '').replace('_answerkey', '').replace('_anserkey', '').replace('_answer_key', '').replace('_answer', '').replace('_answers', '').replace('_letter', '').replace('key_', '').replace('answerkey', '').replace('anserkey', '').replace('answer_key', '')
        
        # Calculate similarity ratios
        ratio1 = SequenceMatcher(None, test_stem_lower, key_stem_lower).ratio()
        ratio2 = SequenceMatcher(None, test_base, key_base).ratio()
        ratio3 = SequenceMatcher(None, test_stem_lower, key_base).ratio()
        ratio4 = SequenceMatcher(None, test_base, key_stem_lower).ratio()
        
        # Use the best ratio
        max_ratio = max(ratio1, ratio2, ratio3, ratio4)
        
        # Also check if one contains the other (partial match)
        if test_stem_lower in key_stem_lower or key_stem_lower in test_stem_lower:
            max_ratio = max(max_ratio, 0.7)  # Boost partial matches
        if test_base in key_base or key_base in test_base:
            max_ratio = max(max_ratio, 0.7)
        
        # Boost if test filename appears in key filename
        if test_stem_lower.replace('_', '') in key_stem_lower.replace('_', ''):
            max_ratio = max(max_ratio, 0.8)
        
        if max_ratio > best_ratio:
            best_ratio = max_ratio
            best_match = key_file
    
    # Return best match if similarity is above threshold
    if best_match and best_ratio >= 0.3:  # Lowered threshold to be more permissive
        print(f"  [OK] Found similarity match: {best_match.name} (ratio: {best_ratio:.2f})")
        return best_match
    
    print(f"  [FAIL] No matching key file found (best ratio: {best_ratio:.2f})")
    return None


def calculate_score(user_answers: Dict[str, str], answer_key: Dict[int, str], questions: List[Question]) -> Dict:
    """
    Calculate score based on user answers and answer key
    Returns a dictionary with score details
    """
    total_questions = len(questions)
    correct = 0
    incorrect = 0
    unanswered = 0
    results = {}
    
    for q in questions:
        question_num = q.number
        user_answer = user_answers.get(str(question_num), "").strip()
        correct_answer = answer_key.get(question_num, "")
        
        if not user_answer:
            unanswered += 1
            results[question_num] = {
                "correct": False,
                "user_answer": "No answer",
                "correct_answer": correct_answer if correct_answer else "Unknown",
                "status": "unanswered"
            }
        elif correct_answer:
            # For multiple choice, compare answer letters
            if q.type == "multiple_choice":
                # User answer is now just the letter (A, B, C, D, E)
                user_letter = user_answer.strip().upper()
                
                # Validate it's a valid letter
                if user_letter not in ['A', 'B', 'C', 'D', 'E']:
                    # Fallback: try to extract letter if format is unexpected
                    letter_match = re.search(r'^([A-E])', user_answer, re.IGNORECASE)
                    if letter_match:
                        user_letter = letter_match.group(1).upper()
                    else:
                        user_letter = None
                
                if user_letter and user_letter == correct_answer.upper():
                    correct += 1
                    results[question_num] = {
                        "correct": True,
                        "user_answer": user_letter,
                        "correct_answer": correct_answer,
                        "status": "correct"
                    }
                else:
                    incorrect += 1
                    results[question_num] = {
                        "correct": False,
                        "user_answer": user_letter if user_letter else user_answer,
                        "correct_answer": correct_answer,
                        "status": "incorrect"
                    }
            else:
                # For short answer, do fuzzy matching
                if user_answer.lower().strip() == correct_answer.lower().strip():
                    correct += 1
                    results[question_num] = {
                        "correct": True,
                        "user_answer": user_answer,
                        "correct_answer": correct_answer,
                        "status": "correct"
                    }
                else:
                    incorrect += 1
                    results[question_num] = {
                        "correct": False,
                        "user_answer": user_answer,
                        "correct_answer": correct_answer,
                        "status": "incorrect"
                    }
        else:
            # No answer key for this question
            results[question_num] = {
                "correct": None,
                "user_answer": user_answer,
                "correct_answer": "No key available",
                "status": "no_key"
            }
    
    score_percentage = (correct / total_questions * 100) if total_questions > 0 else 0
    
    return {
        "total": total_questions,
        "correct": correct,
        "incorrect": incorrect,
        "unanswered": unanswered,
        "score_percentage": round(score_percentage, 2),
        "results": results
    }


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page - list available PDF tests"""
    pdf_files = []
    if TEST_DIR.exists():
        for pdf_file in TEST_DIR.glob("*.pdf"):
            pdf_files.append({
                "name": pdf_file.name,
                "path": str(pdf_file)
            })
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "pdf_files": pdf_files
    })


@app.get("/results/{answer_filename}", response_class=HTMLResponse)
async def view_results(request: Request, answer_filename: str):
    """View detailed results HTML file"""
    answer_path = ANSWER_DIR / answer_filename
    
    if not answer_path.exists():
        raise HTTPException(status_code=404, detail="Results file not found")
    
    try:
        with open(answer_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading results file: {str(e)}")


@app.get("/test/{pdf_name}", response_class=HTMLResponse)
async def show_test(request: Request, pdf_name: str):
    """Display test questions from PDF"""
    pdf_path = TEST_DIR / pdf_name
    
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="PDF file not found")
    
    try:
        questions = extract_questions_from_pdf(pdf_path)
        print(f"Extracted {len(questions)} questions")  # Debug
        # Debug: Print question details for first 3 questions
        for q in questions[:3]:
            print(f"  Q{q.number}: {q.type} - {len(q.choices)} choices")
            print(f"    Text: {q.text[:100]}..." if len(q.text) > 100 else f"    Text: {q.text}")
            if q.choices:
                for i, choice in enumerate(q.choices[:4]):
                    print(f"    {['A','B','C','D','E'][i]}. {choice[:60]}...")
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error processing PDF: {error_details}")  # Debug output
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")
    
    # Convert questions to dict for template
    questions_data = []
    try:
        for q in questions:
            questions_data.append({
                "number": q.number,
                "text": q.text or "",
                "type": q.type,
                "choices": q.choices or []
            })
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error converting questions: {error_details}")
        raise HTTPException(status_code=500, detail=f"Error preparing questions: {str(e)}")
    
    try:
        return templates.TemplateResponse("test.html", {
            "request": request,
            "pdf_name": pdf_name,
            "questions": questions_data
        })
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error rendering template: {error_details}")
        raise HTTPException(status_code=500, detail=f"Error rendering template: {str(e)}")


@app.post("/submit/{pdf_name}")
async def submit_answers(pdf_name: str, request: Request):
    """Save user answers, calculate score, and display results"""
    form_data = await request.form()
    
    # Extract answers
    answers = {}
    for key, value in form_data.items():
        if key.startswith("answer_"):
            question_num = key.replace("answer_", "")
            answers[question_num] = value
    
    # Get questions from the test PDF
    pdf_path = TEST_DIR / pdf_name
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="PDF file not found")
    
    try:
        questions = extract_questions_from_pdf(pdf_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")
    
    # Try to find and load answer key from KEY_DIR
    print(f"\n{'='*70}")
    print(f"Processing submission for: {pdf_name}")
    print(f"{'='*70}")
    print(f"Looking for answer key in: {KEY_DIR}")
    
    # List all available key files for debugging
    if KEY_DIR.exists():
        available_keys = []
        if EXCEL_AVAILABLE:
            available_keys.extend(KEY_DIR.glob("*.xlsx"))
            available_keys.extend(KEY_DIR.glob("*.xls"))
        available_keys.extend(KEY_DIR.glob("*.pdf"))
        # Filter out temporary Excel files
        available_keys = [k for k in available_keys if not k.name.startswith('~$')]
        print(f"Available key files ({len(available_keys)}):")
        for k in available_keys:
            print(f"  - {k.name}")
    else:
        print(f"ERROR: Key directory does not exist: {KEY_DIR}")
    
    key_path = find_matching_key_file(pdf_name)
    answer_key = {}
    key_found = False
    
    if key_path and key_path.exists():
        print(f"\n[OK] Found matching key file: {key_path.name}")
        print(f"  Full path: {key_path}")
        print(f"  File type: {'Excel' if key_path.suffix.lower() in ['.xlsx', '.xls'] else 'PDF'}")
        try:
            # Determine file type and extract accordingly
            if key_path.suffix.lower() in ['.xlsx', '.xls']:
                if not EXCEL_AVAILABLE:
                    print(f"  [ERROR] Excel support not available. Install pandas: pip install pandas openpyxl")
                    key_found = False
                else:
                    answer_key = extract_answer_key_from_excel(key_path)
                    key_found = len(answer_key) > 0
                    print(f"[OK] Extracted {len(answer_key)} answers from Excel file")
                    if answer_key:
                        print(f"  Sample answers: {dict(list(answer_key.items())[:5])}")
                    else:
                        print(f"  [WARN] No answers extracted from Excel file. Check file format.")
            else:
                # PDF file
                answer_key = extract_answer_key_from_pdf(key_path)
                key_found = len(answer_key) > 0
                print(f"[OK] Extracted {len(answer_key)} answers from PDF file")
                if answer_key:
                    print(f"  Sample answers: {dict(list(answer_key.items())[:5])}")
                else:
                    print(f"  [WARN] No answers extracted from PDF file. Check PDF format.")
        except Exception as e:
            print(f"  [ERROR] Error extracting answers: {e}")
            import traceback
            traceback.print_exc()
            key_found = False
        
        # Save answer key as HTML file
        if key_found:
            try:
                key_html_path = ANSWER_DIR / f"{Path(pdf_name).stem}_answer_key.html"
                save_answer_key_html(key_path, answer_key, key_html_path)
                print(f"[OK] Answer key HTML saved to: {key_html_path}")
            except Exception as e:
                print(f"  [WARN] Could not save answer key HTML: {e}")
    else:
        print(f"\n[FAIL] No matching key file found for: {pdf_name}")
        print(f"  Searched in: {KEY_DIR}")
        if KEY_DIR.exists():
            available_keys = []
            if EXCEL_AVAILABLE:
                available_keys.extend(KEY_DIR.glob("*.xlsx"))
                available_keys.extend(KEY_DIR.glob("*.xls"))
            available_keys.extend(KEY_DIR.glob("*.pdf"))
            available_keys = [k for k in available_keys if not k.name.startswith('~$')]
            print(f"  Available key files: {[k.name for k in available_keys]}")
        else:
            print(f"  ERROR: Key directory does not exist: {KEY_DIR}")
    
    # Calculate score if key is available
    score_data = None
    if key_found:
        print(f"Calculating score for {len(answers)} user answers against {len(answer_key)} answer key entries...")
        score_data = calculate_score(answers, answer_key, questions)
        print(f"[OK] Score calculated: {score_data['correct']}/{score_data['total']} correct ({score_data['score_percentage']}%)")
    else:
        print("[WARN] Cannot calculate score: No answer key available")
    
    # Create answer file name based on PDF name
    pdf_stem = Path(pdf_name).stem
    answer_filename = f"{pdf_stem}_answers.html"
    answer_path = ANSWER_DIR / answer_filename
    
    # Generate HTML content with scores
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test Results: {pdf_name}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 900px;
            margin: 40px auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            margin-bottom: 10px;
        }}
        .pdf-name {{
            color: #666;
            margin-bottom: 30px;
        }}
        .score-summary {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
            border-radius: 8px;
            margin-bottom: 30px;
            text-align: center;
        }}
        .score-summary h2 {{
            margin: 0 0 15px 0;
            font-size: 24px;
        }}
        .score-details {{
            display: flex;
            justify-content: space-around;
            margin-top: 20px;
        }}
        .score-item {{
            text-align: center;
        }}
        .score-item .number {{
            font-size: 32px;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        .score-item .label {{
            font-size: 14px;
            opacity: 0.9;
        }}
        .answer-item {{
            margin-bottom: 20px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 5px;
            border-left: 4px solid #667eea;
        }}
        .answer-item.correct {{
            border-left-color: #28a745;
            background: #d4edda;
        }}
        .answer-item.incorrect {{
            border-left-color: #dc3545;
            background: #f8d7da;
        }}
        .answer-item.unanswered {{
            border-left-color: #ffc107;
            background: #fff3cd;
        }}
        .question-number {{
            font-weight: 700;
            color: #667eea;
            margin-bottom: 5px;
        }}
        .answer-item.correct .question-number {{
            color: #28a745;
        }}
        .answer-item.incorrect .question-number {{
            color: #dc3545;
        }}
        .answer-text {{
            color: #333;
            margin-left: 20px;
            margin-top: 5px;
        }}
        .correct-answer {{
            color: #28a745;
            font-weight: 600;
            margin-top: 5px;
            margin-left: 20px;
        }}
        .status-badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
            margin-left: 10px;
        }}
        .status-correct {{
            background: #28a745;
            color: white;
        }}
        .status-incorrect {{
            background: #dc3545;
            color: white;
        }}
        .status-unanswered {{
            background: #ffc107;
            color: #333;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Test Results</h1>
        <p class="pdf-name">PDF: {pdf_name}</p>
"""
    
    # Add score summary if available
    if score_data:
        html_content += f"""
        <div class="score-summary">
            <h2>Your Score: {score_data['score_percentage']}%</h2>
            <div class="score-details">
                <div class="score-item">
                    <div class="number">{score_data['correct']}</div>
                    <div class="label">Correct</div>
                </div>
                <div class="score-item">
                    <div class="number">{score_data['incorrect']}</div>
                    <div class="label">Incorrect</div>
                </div>
                <div class="score-item">
                    <div class="number">{score_data['unanswered']}</div>
                    <div class="label">Unanswered</div>
                </div>
                <div class="score-item">
                    <div class="number">{score_data['total']}</div>
                    <div class="label">Total</div>
                </div>
            </div>
        </div>
"""
    elif key_path:
        html_content += """
        <div style="background: #fff3cd; padding: 15px; border-radius: 8px; margin-bottom: 20px; color: #856404;">
            <strong>Note:</strong> Answer key file found but could not extract answers. Please check the key file format.
        </div>
"""
    else:
        html_content += """
        <div style="background: #d1ecf1; padding: 15px; border-radius: 8px; margin-bottom: 20px; color: #0c5460;">
            <strong>Note:</strong> No answer key file found. Answers saved but not scored.
        </div>
"""
    
    # Add wrong answers section if there are incorrect answers
    if score_data:
        wrong_questions = []
        unanswered_questions = []
        for q_num, result in score_data['results'].items():
            if result.get('status') == 'incorrect':
                wrong_questions.append({
                    'number': q_num,
                    'user_answer': result.get('user_answer', ''),
                    'correct_answer': result.get('correct_answer', '')
                })
            elif result.get('status') == 'unanswered':
                unanswered_questions.append({
                    'number': q_num,
                    'correct_answer': result.get('correct_answer', '')
                })
        
        if wrong_questions:
            html_content += """
        <div class="wrong-answers-section" style="margin-bottom: 30px;">
            <h2 style="color: #dc3545; margin-bottom: 20px; border-bottom: 2px solid #dc3545; padding-bottom: 10px;">
                Incorrect Answers ({count})
            </h2>
            <table style="width: 100%; border-collapse: collapse;">
                <thead>
                    <tr style="background: #f8d7da; color: #721c24;">
                        <th style="padding: 12px; text-align: left; border: 1px solid #f5c6cb;">Question #</th>
                        <th style="padding: 12px; text-align: left; border: 1px solid #f5c6cb;">Your Answer</th>
                        <th style="padding: 12px; text-align: left; border: 1px solid #f5c6cb;">Correct Answer</th>
                    </tr>
                </thead>
                <tbody>
""".replace('{count}', str(len(wrong_questions)))
            
            # Format answer helper function
            def format_answer_display(q_num: int, ans: str) -> str:
                """Format answer as '3. B.' format"""
                if ans and ans.strip():
                    ans_letter = ans.strip().upper()
                    if len(ans_letter) == 1 and ans_letter in ['A', 'B', 'C', 'D', 'E']:
                        return f"{q_num}. {ans_letter}."
                    else:
                        letter_match = re.search(r'([A-E])', ans_letter)
                        if letter_match:
                            return f"{q_num}. {letter_match.group(1)}."
                return f"{q_num}. {ans}" if ans else f"{q_num}. (No answer)"
            
            for wrong in sorted(wrong_questions, key=lambda x: x['number']):
                formatted_user = format_answer_display(wrong['number'], wrong['user_answer'])
                formatted_correct = format_answer_display(wrong['number'], wrong['correct_answer'])
                html_content += f"""
                    <tr style="background: #fff; border-bottom: 1px solid #f5c6cb;">
                        <td style="padding: 10px; border: 1px solid #f5c6cb; font-weight: 600; color: #dc3545;">{wrong['number']}</td>
                        <td style="padding: 10px; border: 1px solid #f5c6cb; color: #721c24;">{formatted_user}</td>
                        <td style="padding: 10px; border: 1px solid #f5c6cb; color: #28a745; font-weight: 600;">{formatted_correct}</td>
                    </tr>
"""
            
            html_content += """
                </tbody>
            </table>
        </div>
"""
        
        if unanswered_questions:
            # Format unanswered questions with correct answers
            unanswered_list = []
            for q in sorted(unanswered_questions, key=lambda x: x['number']):
                q_num = q['number']
                correct_ans = q.get('correct_answer', '')
                if correct_ans and correct_ans not in ["Unknown", ""]:
                    # Format as "3. B."
                    ans_letter = correct_ans.strip().upper()
                    if len(ans_letter) == 1 and ans_letter in ['A', 'B', 'C', 'D', 'E']:
                        formatted = f"{q_num}. {ans_letter}."
                    else:
                        letter_match = re.search(r'([A-E])', ans_letter)
                        formatted = f"{q_num}. {letter_match.group(1)}." if letter_match else f"{q_num}. {correct_ans}"
                    unanswered_list.append(f"Q{q_num}: {formatted}")
                else:
                    unanswered_list.append(f"Q{q_num}")
            
            html_content += f"""
        <div class="unanswered-section" style="margin-bottom: 30px;">
            <h3 style="color: #ffc107; margin-bottom: 15px;">Unanswered Questions ({len(unanswered_questions)})</h3>
            <div style="color: #856404; line-height: 1.8;">
                {'<br>'.join(unanswered_list)}
            </div>
        </div>
"""
    
    html_content += """
        <div class="answers">
            <h2 style="color: #333; margin-bottom: 20px; border-bottom: 2px solid #667eea; padding-bottom: 10px;">
                All Answers
            </h2>
"""
    
    # Sort answers by question number
    sorted_answers = sorted(answers.items(), key=lambda x: int(x[0]) if x[0].isdigit() else 0)
    
    # Format answer for display: "3 B" -> "3. B."
    def format_answer(question_num: str, answer: str) -> str:
        """Format answer as '3. B.' format"""
        if answer and answer.strip():
            # Extract just the letter if it's a full answer
            answer_letter = answer.strip().upper()
            if len(answer_letter) == 1 and answer_letter in ['A', 'B', 'C', 'D', 'E']:
                return f"{question_num}. {answer_letter}."
            else:
                # Try to extract letter from answer
                letter_match = re.search(r'([A-E])', answer_letter)
                if letter_match:
                    return f"{question_num}. {letter_match.group(1)}."
        return f"{question_num}. {answer}"
    
    for question_num, answer in sorted_answers:
        q_num = int(question_num) if question_num.isdigit() else 0
        result = score_data['results'].get(q_num, {}) if score_data else {}
        status = result.get('status', 'no_key')
        correct_answer = result.get('correct_answer', '')
        
        # Format answers for display
        formatted_user_answer = format_answer(question_num, answer)
        formatted_correct_answer = ""
        if correct_answer and correct_answer not in ["No key available", "Unknown", ""]:
            formatted_correct_answer = format_answer(question_num, correct_answer)
        
        status_class = status if status in ['correct', 'incorrect', 'unanswered'] else ''
        status_label = {
            'correct': '✓ Correct',
            'incorrect': '✗ Incorrect',
            'unanswered': '? Unanswered',
            'no_key': ''
        }.get(status, '')
        
        html_content += f"""
            <div class="answer-item {status_class}">
                <div class="question-number">
                    Question {question_num}
                    {f'<span class="status-badge status-{status}">{status_label}</span>' if status_label else ''}
                </div>
                <div class="answer-text"><strong>Your Answer:</strong> {formatted_user_answer}</div>
"""
        if formatted_correct_answer:
            html_content += f"""
                <div class="correct-answer"><strong>Correct Answer:</strong> {formatted_correct_answer}</div>
"""
        html_content += """
            </div>
"""
    
    html_content += """
        </div>
    </div>
</body>
</html>
"""
    
    # Save HTML file
    try:
        with open(answer_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")
    
    return templates.TemplateResponse("success.html", {
        "request": request,
        "pdf_name": pdf_name,
        "answer_file": answer_filename,
        "answer_path": str(answer_path),
        "score_data": score_data,
        "key_found": key_found
    })


if __name__ == "__main__":
    import uvicorn
    import sys
    
    print("=" * 50)
    print("Starting Interactive Test UI Application")
    print("=" * 50)
    print(f"Server will be available at: http://localhost:8000")
    print(f"Test directory: {TEST_DIR}")
    print(f"Key directory: {KEY_DIR}")
    print(f"Answer directory: {ANSWER_DIR}")
    print("=" * 50)
    print("Press Ctrl+C to stop the server")
    print("=" * 50)
    print()
    
    try:
        uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
    except KeyboardInterrupt:
        print("\nServer stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\nERROR: Failed to start server: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure port 8000 is not already in use")
        print("2. Check that all dependencies are installed: pip install -r requirements.txt")
        print("3. Verify Python version is 3.7 or higher")
        sys.exit(1)

