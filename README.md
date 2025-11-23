# USABO Test UI

An interactive web-based test application for USABO (USA Biology Olympiad) exams. This application allows users to take online tests from PDF files and automatically scores their answers using Excel or PDF answer keys.

## Features

- 📝 **PDF Test Extraction**: Automatically extracts questions and multiple-choice options from PDF test files
- ✅ **Excel Answer Key Support**: Reads answer keys from Excel files (.xlsx, .xls) with flexible column naming
- 📄 **PDF Answer Key Support**: Also supports PDF answer keys with text-based extraction
- 🎯 **Automatic Matching**: Intelligently matches test files with their corresponding answer keys
- 📊 **Score Calculation**: Automatically calculates scores with detailed breakdown
- 📈 **Detailed Results**: Shows correct, incorrect, and unanswered questions with side-by-side comparison
- 💾 **Answer Saving**: Saves user answers and answer keys as HTML files for review

## Requirements

- Python 3.7+
- FastAPI
- pdfplumber
- pandas
- openpyxl
- uvicorn

## Installation

1. Clone this repository:
```bash
git clone https://github.com/YOUR_USERNAME/usabo.git
cd usabo
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Setup

1. **Create Directory Structure**:
   - Test PDF files: `C:\Users\nieli\Documents\USABO\Test\`
   - Answer key files: `C:\Users\nieli\Documents\USABO\Key\` (Excel or PDF)
   - User answers: `C:\Users\nieli\Documents\USABO\UserAnswer\` (auto-created)

2. **Configure Paths** (if needed):
   Edit `test_ui_app.py` and update the directory paths:
   ```python
   TEST_DIR = Path(r"C:\Users\nieli\Documents\USABO\Test")
   KEY_DIR = Path(r"C:\Users\nieli\Documents\USABO\Key")
   ANSWER_DIR = Path(r"C:\Users\nieli\Documents\USABO\UserAnswer")
   ```

## Usage

### Start the Server

**Option 1: Using the batch file**
```bash
start_server.bat
```

**Option 2: Using Python directly**
```bash
python test_ui_app.py
```

The server will start at: **http://localhost:8000**

### Taking a Test

1. Open your browser and navigate to `http://localhost:8000`
2. Select a test PDF from the list
3. Answer the questions by selecting radio buttons
4. Click "Submit Answers"
5. View your score and detailed results

## Answer Key Format

### Excel Format
The Excel answer key files should have:
- **Column 1**: Question numbers (1, 2, 3, ...)
- **Column 2**: Answer letters (A, B, C, D, E)

Column names can be:
- "Questions" / "Answers"
- "Question" / "Answer"
- Or any similar variation (case-insensitive)

### PDF Format
PDF answer keys are extracted using text patterns. Supported formats:
- `1. A` or `1) A` or `1 A`
- `Question 1: A`
- Filled checkboxes: `[X] A.` or `[✓] A.`
- Yellow highlighted answers (if present)

## File Naming Convention

The application automatically matches test files with answer keys using filename similarity:

- Test: `2003_OpenExam.pdf` → Key: `2003_OpenExam_AnserKey.xlsx`
- Test: `2010_OpenExam.pdf` → Key: `2010_OpenExam_AnserKey.xlsx`

The matching is flexible and handles:
- Case variations
- Typo variations (e.g., "AnserKey" vs "AnswerKey")
- Different file extensions (.xlsx, .xls, .pdf)

## Project Structure

```
usabo/
├── test_ui_app.py          # Main FastAPI application
├── templates/              # HTML templates
│   ├── index.html         # Test list page
│   ├── test.html          # Test taking page
│   └── success.html       # Results page
├── start_server.bat       # Windows startup script
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## API Endpoints

- `GET /` - List available test PDFs
- `GET /test/{pdf_name}` - Display test questions
- `POST /submit/{pdf_name}` - Submit answers and get results
- `GET /results/{answer_filename}` - View detailed results HTML

## Features in Detail

### Question Extraction
- Handles multi-line question text
- Detects inline choices (`[ ] A.`) and separate-line choices (`A.`)
- Supports questions with 2-5 choices (A, B, C, D, E)

### Answer Key Extraction
- **Excel**: Reads all rows, handles various column names, extracts question numbers and answer letters
- **PDF**: Multiple extraction methods including text patterns and yellow highlight detection
- Validates answer format (A-E only)

### Scoring
- Each correct answer = 1 point
- Shows percentage score
- Lists incorrect answers with user answer vs correct answer
- Lists unanswered questions

## Troubleshooting

### Server won't start
- Check if port 8000 is already in use: `netstat -ano | findstr :8000`
- Kill the process or change the port in `test_ui_app.py`

### Answer key not found
- Ensure answer key file is in the `Key` directory
- Check filename similarity with test file
- Verify file extension (.xlsx, .xls, or .pdf)

### No answers extracted from Excel
- Verify Excel file has at least 2 columns
- Check that column names contain "Question" and "Answer" (or similar)
- Ensure answer letters are A, B, C, D, or E

## License

This project is open source and available for educational purposes.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
