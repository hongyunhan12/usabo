# Chinese Flashcard App

An interactive web-based flashcard application similar to Quizlet for learning Chinese words. The app reads Chinese words from an Excel file and displays them as beautiful, flipable flashcards.

## Features

- 📚 **Excel Database**: Reads Chinese words from Excel file
- 🎴 **Interactive Flashcards**: Click to flip cards and see pronunciation and meaning
- ⌨️ **Keyboard Navigation**: Use arrow keys to navigate, space/Enter to flip
- 🎨 **Modern UI**: Beautiful gradient design with smooth animations
- 📱 **Responsive**: Works on desktop and mobile devices

## Requirements

- Python 3.7+
- FastAPI
- pandas
- openpyxl
- uvicorn

All dependencies are already in `requirements.txt`.

## Installation

1. Make sure you have installed the dependencies:
```bash
pip install -r requirements.txt
```

2. Ensure your Excel file is located at:
```
C:\Users\nieli\Documents\Flashcard\Chinese_words_list.xlsx
```

The Excel file should have the following columns:
- `word`: Chinese word (e.g., "的", "一", "不")
- `sound_meaning`: Combined pronunciation and meaning (e.g., "de/di2/di4      (possessive particle)/of, really and truly, aim/clear")

## Usage

### Option 1: Using the batch file (Windows)
```bash
run_flashcard.bat
```

### Option 2: Using Python directly
```bash
python flashcard_app.py
```

The app will start at: **http://localhost:8001**

## How to Use

1. **Open the app**: Navigate to `http://localhost:8001` in your browser
2. **View the word**: The front of the card shows the Chinese word
3. **Flip the card**: Click on the card or press Space/Enter to see pronunciation and meaning
4. **Navigate**: 
   - Click "上一张" (Previous) or "下一张" (Next) buttons
   - Use Left/Right arrow keys to navigate
   - Use Space or Enter to flip the card

## Excel File Format

The app expects an Excel file with the following structure:

| no | word | occurrence | random | sound_meaning |
|----|------|------------|--------|---------------|
| 1  | 的   | 8302698    | 3.2075 | de/di2/di4      (possessive particle)/of, really and truly, aim/clear |
| 2  | 一   | 3728398    | 4.647855 | yi1     one/1/single/a(n) |

The `sound_meaning` column is automatically parsed:
- **Pronunciation** (first part): Extracted before multiple spaces/tabs
- **Meaning** (second part): Extracted after multiple spaces/tabs

## API Endpoints

- `GET /` - Main flashcard page
- `GET /api/flashcards` - Get all flashcards as JSON
- `GET /api/flashcard/{card_id}` - Get a specific flashcard by ID

## Troubleshooting

### Excel file not found
Make sure the Excel file exists at:
```
C:\Users\nieli\Documents\Flashcard\Chinese_words_list.xlsx
```

If your file is in a different location, edit `flashcard_app.py` and update the `EXCEL_FILE_PATH` variable.

### No cards displayed
- Check that your Excel file has `word` and `sound_meaning` columns
- Verify the file path is correct
- Check the browser console for error messages

### Parsing issues
If pronunciation or meaning are not parsed correctly, the app will still display the data but may show it in a combined format. You can adjust the parsing logic in the `parse_sound_meaning()` function in `flashcard_app.py`.

## Customization

### Change the port
Edit `flashcard_app.py` and modify the port in the `uvicorn.run()` call:
```python
uvicorn.run(app, host="0.0.0.0", port=8001)
```

### Change the Excel file path
Edit `flashcard_app.py` and update:
```python
EXCEL_FILE_PATH = Path(r"YOUR_PATH_HERE")
```

### Customize styling
Edit `templates/flashcard.html` to change colors, fonts, and layout.

## Sharing with Others

Want to share this app with friends, family, or students? Check out:

- **Quick Start Guide**: `QUICK_START_SHARING.md` - Fastest ways to share
- **Full Deployment Guide**: `FLASHCARD_DEPLOYMENT.md` - Complete deployment options

### Quick Options:

1. **Same WiFi Network**: Share your IP address (e.g., `http://192.168.1.100:8001`)
2. **Cloud Deployment**: Deploy to Render.com (free) for public access
3. **Share Files**: Send the app files for others to run locally

See the deployment guides for detailed instructions!

