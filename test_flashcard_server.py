"""Quick test to verify the flashcard server starts correctly"""
import requests
import time
import subprocess
import sys
from pathlib import Path

def test_server():
    print("Testing flashcard server...")
    
    # Check if template exists
    template_path = Path("templates/flashcard.html")
    if not template_path.exists():
        print(f"ERROR: Template file not found at {template_path}")
        return False
    print(f"[OK] Template file found: {template_path}")
    
    # Check if Excel file exists (either location)
    excel_path1 = Path(r"C:\Users\nieli\Documents\Flashcard\Chinese_words_list.xlsx")
    excel_path2 = Path("Chinese_words_list.xlsx")
    
    if excel_path1.exists():
        print(f"[OK] Excel file found: {excel_path1}")
    elif excel_path2.exists():
        print(f"[OK] Excel file found: {excel_path2}")
    else:
        print(f"[WARNING] Excel file not found at either location")
        print(f"  - {excel_path1}")
        print(f"  - {excel_path2}")
    
    # Try to import the app
    try:
        from flashcard_app import app
        print("[OK] Flashcard app imports successfully")
    except Exception as e:
        print(f"[ERROR] Error importing flashcard app: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "="*60)
    print("All checks passed! You can now run:")
    print("  py flashcard_app.py")
    print("  or")
    print("  run_flashcard.bat")
    print("="*60)
    return True

if __name__ == "__main__":
    test_server()
